---
name: kv-store-grpc
description: Guidance for building gRPC-based key-value store services in Python. This skill should be used when tasks involve creating gRPC servers, defining protocol buffer schemas, or implementing key-value storage APIs with gRPC. Covers proto file creation, code generation, server implementation, and verification strategies.
---

# gRPC Key-Value Store Implementation

## Overview

This skill provides procedural knowledge for implementing gRPC-based key-value store services in Python. It covers the complete workflow from proto file definition through server implementation and verification.

## Workflow

### Step 1: Environment Setup

Install the required gRPC packages with specific versions if provided:

```bash
pip install grpcio==<version> grpcio-tools==<version>
```

If no versions are specified, install the latest:

```bash
pip install grpcio grpcio-tools
```

**Verification**: Run `pip show grpcio grpcio-tools` to confirm installation.

### Step 2: Define the Protocol Buffer Schema

Create a `.proto` file defining the service and messages.

**Key elements to include:**
- `syntax = "proto3";` declaration
- `package` declaration (best practice for larger projects)
- Service definition with RPC methods
- Message definitions for requests and responses

**Common proto patterns for key-value stores:**

```protobuf
syntax = "proto3";

package kvstore;

service KVStore {
    rpc SetVal(SetRequest) returns (SetResponse);
    rpc GetVal(GetRequest) returns (GetResponse);
}

message SetRequest {
    string key = 1;
    int32 value = 2;
}

message SetResponse {
    bool success = 1;
}

message GetRequest {
    string key = 1;
}

message GetResponse {
    int32 value = 1;
}
```

**Common pitfall**: Forgetting the package declaration - while not strictly required, it prevents naming conflicts in larger projects.

### Step 3: Generate Python gRPC Code

Run the protobuf compiler to generate Python code:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. <service_name>.proto
```

This generates two files:
- `<service_name>_pb2.py` - Message classes
- `<service_name>_pb2_grpc.py` - Service stubs and base classes

**Verification**: Confirm both files exist and contain the expected classes by reading them.

**Important**: Examine the generated `*_pb2_grpc.py` file to understand:
- The servicer base class to inherit from
- Method signatures to implement
- How to add the servicer to the server

### Step 4: Implement the Server

Create a server file that:
1. Imports the generated modules
2. Implements the servicer class
3. Sets up and starts the gRPC server

**Key implementation details:**

```python
import grpc
from concurrent import futures
import <service_name>_pb2
import <service_name>_pb2_grpc

class KVStoreServicer(<service_name>_pb2_grpc.<ServiceName>Servicer):
    def __init__(self):
        self.store = {}

    def SetVal(self, request, context):
        self.store[request.key] = request.value
        return <service_name>_pb2.SetResponse(success=True)

    def GetVal(self, request, context):
        value = self.store.get(request.key, 0)  # Default to 0 for missing keys
        return <service_name>_pb2.GetResponse(value=value)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    <service_name>_pb2_grpc.add_<ServiceName>Servicer_to_server(
        KVStoreServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051", flush=True)  # flush=True is important!
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```

**Critical pitfall - Output buffering**: When running the server in the background, Python buffers stdout by default. To see output:
- Use `print(..., flush=True)` for all print statements
- Or run Python with `-u` flag: `python -u server.py`
- Or use the `logging` module instead of print

### Step 5: Start the Server

Run the server in the background:

```bash
python server.py &
```

Or with unbuffered output:

```bash
python -u server.py &
```

### Step 6: Verify the Server

**Preferred approach**: Write and run a test client. This is more reliable than system tools.

**Common mistake**: Attempting to use system tools like `netstat`, `ss`, `lsof`, or `ps` to verify the server. These tools may not be available in all environments. Instead, test the server directly with a client.

**Test client template:**

```python
import grpc
import <service_name>_pb2
import <service_name>_pb2_grpc

def test_kv_store():
    channel = grpc.insecure_channel('localhost:50051')
    stub = <service_name>_pb2_grpc.<ServiceName>Stub(channel)

    # Test SetVal
    set_response = stub.SetVal(<service_name>_pb2.SetRequest(key="test_key", value=42))
    print(f"SetVal response: success={set_response.success}")

    # Test GetVal
    get_response = stub.GetVal(<service_name>_pb2.GetRequest(key="test_key"))
    print(f"GetVal response: value={get_response.value}")

    # Test non-existent key (should return default value)
    get_missing = stub.GetVal(<service_name>_pb2.GetRequest(key="missing_key"))
    print(f"GetVal missing key: value={get_missing.value}")

if __name__ == '__main__':
    test_kv_store()
```

**Comprehensive testing should verify:**
- Setting and retrieving values
- Retrieving non-existent keys (verify default behavior)
- Overwriting existing keys
- Multiple different keys

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Print statements not appearing when server runs in background | Use `flush=True` or run with `python -u` |
| Trying to use netstat/ss/lsof to verify server | Write a test client instead - more reliable |
| Missing package declaration in proto | Add `package <name>;` after syntax declaration |
| Not examining generated code before implementing | Read `*_pb2_grpc.py` to understand the servicer interface |
| Incomplete verification | Test all operations including edge cases |
| No default value for missing keys | Use `dict.get(key, default)` pattern |

## Edge Cases to Consider

- **Missing keys**: Return a sensible default (often 0 or empty string)
- **Empty keys**: Consider whether to validate or allow
- **Type boundaries**: Protobuf enforces int32 bounds automatically
- **Connection failures**: Client should handle gRPC exceptions
- **Server shutdown**: Consider implementing graceful shutdown for production

## Efficiency Tips

1. **Verification strategy**: Go directly to application-level testing with a client rather than system-level inspection tools
2. **Examine generated code**: Read the generated `*_pb2_grpc.py` file before implementing to understand method signatures
3. **Test incrementally**: Verify each step works before moving to the next
4. **Keep test clients**: Do not delete test clients - they serve as useful debugging tools
