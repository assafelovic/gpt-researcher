# Embed Script

The embed script enables you to embed the latest GPTR NextJS app into your web app.

To achieve this, simply add these 2 script tags into your HTML:

```javascript
<script>localStorage.setItem("GPTR_API_URL", "http://localhost:8000");</script>
<script src="https://app.gptr.dev/embed.js"></script>
```

Here's a minmalistic HTML example (P.S. You can also save this as an index.html file and open it with your Web Browser)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPT Researcher Embed Demo</title>
</head>
<body style="margin: 0; padding: 0;">
    <!-- GPT Researcher Embed -->
    <script>localStorage.setItem("GPTR_API_URL", "http://localhost:8000");</script>
    <script src="https://app.gptr.dev/embed.js"></script>
</body>
</html>
```

This example relies on setting a custom localstorage value for `GPTR_API_URL`. To point your embedded frontend at a custom GPTR API Server, feel free to edit `http://localhost:8000` to your custom GPTR server address.