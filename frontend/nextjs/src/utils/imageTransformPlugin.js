// rollup-image-transform-plugin.js
export default function imageTransformPlugin() {
    return {
      name: 'image-transform',
      transform(code) {
        // Replace all relative image paths with absolute URLs
        return code.replace(
          /'img\/([^']+)'/g, 
          "'https://gptr.app/img/$1'"
        ).replace(
          /"img\/([^"]+)"/g, 
          '"https://gptr.app/img/$1"'
        );
      }
    };
  }