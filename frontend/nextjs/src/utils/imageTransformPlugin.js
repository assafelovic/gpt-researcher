// imageTransformPlugin.js
export default function imageTransformPlugin() {
  return {
    name: 'image-transform',
    transform(code) {
      // Add more patterns to catch different image path formats
      return code.replace(
        /['"]\/img\/([^'"]+)['"]/g,  // Also catch paths starting with /
        "'https://gptr.app/img/$1'"
      ).replace(
        /['"]img\/([^'"]+)['"]/g,    // Catch relative paths
        "'https://gptr.app/img/$1'"
      );
    }
  };
}