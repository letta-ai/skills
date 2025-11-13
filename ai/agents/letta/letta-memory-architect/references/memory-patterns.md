# Memory Block Patterns by Domain

## Customer Support Agent

```yaml
persona:
  label: persona
  description: "Your role as customer support agent, including communication style and escalation criteria."
  value: |
    I am a customer support agent for [Company]. I respond professionally,
    empathetically, and efficiently. I escalate to humans when: [criteria].

company_policies:
  label: company_policies
  description: "Company policies and procedures. Reference when handling returns, warranties, or service requests."
  read_only: true
  value: |
    Return Policy: [details]
    Warranty: [details]
    Service Terms: [details]

product_knowledge:
  label: product_knowledge
  description: "Product features and common solutions. Update when learning new troubleshooting steps."
  value: |
    Product A: [features, common issues]
    Product B: [features, common issues]

customer:
  label: customer
  description: "Current customer's information and interaction history. Update as you learn more about them."
  value: |
    Name: [extracted from conversation]
    Issue: [current problem]
    History: [relevant past interactions]
```

## Coding Assistant

```yaml
persona:
  label: persona
  description: "Your approach to coding assistance and communication with developers."
  value: |
    I help write clean, maintainable code. I explain my reasoning,
    suggest best practices, and ask clarifying questions.

project_context:
  label: project_context
  description: "Current project architecture and goals. Update as you learn about the codebase."
  value: |
    Project: [name]
    Stack: [technologies]
    Architecture: [patterns]
    Current Focus: [active work]

coding_standards:
  label: coding_standards
  description: "Team coding standards and review checklist. Reference before making suggestions."
  read_only: true
  value: |
    Style Guide: [details]
    Testing Requirements: [coverage, patterns]
    Review Checklist: [items]

current_task:
  label: current_task
  description: "Active coding task and implementation progress. Update as work advances."
  value: |
    Task: [description]
    Approach: [planned solution]
    Progress: [completed steps]
    Blockers: [current issues]
```

## Personal Assistant

```yaml
persona:
  label: persona
  description: "Your role as personal assistant and communication preferences."
  value: |
    I help manage your schedule, remind you of tasks, and provide
    proactive assistance. I'm concise unless you ask for detail.

schedule:
  label: schedule
  description: "Upcoming appointments and commitments. Update when scheduling or rescheduling."
  value: |
    Today: [appointments]
    This Week: [commitments]
    Upcoming: [notable events]

preferences:
  label: preferences
  description: "User's preferences and decision-making criteria. Update as you learn more."
  value: |
    Communication: [style preferences]
    Priorities: [what matters most]
    Constraints: [time zones, availability]