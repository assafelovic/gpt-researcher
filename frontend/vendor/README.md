# Vendored frontend assets

These pinned browser dependencies are served locally so a self-hosted GPT
Researcher page does not contact a third-party CDN during page load.

| Package | Version | Upstream asset source |
| --- | --- | --- |
| Bootstrap | 4.5.2 | `cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/css/bootstrap.min.css` |
| Font Awesome Free | 6.5.1 | `cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/` |
| Showdown | 1.9.1 | `cdn.jsdelivr.net/npm/showdown@1.9.1/dist/showdown.min.js` |
| DOMPurify | 3.2.6 | `cdn.jsdelivr.net/npm/dompurify@3.2.6/dist/purify.min.js` |

The corresponding license texts are stored in this directory. Font Awesome's
CSS references several font variants, but this frontend uses only the solid and
brands families, so only those WOFF2 files are included.
