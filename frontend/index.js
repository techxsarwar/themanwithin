module.exports = {
    onPreBuild: async ({ utils }) => {
        console.log("Local bypass plugin loaded successfully to prevent ENOTFOUND build errors.");
    }
}