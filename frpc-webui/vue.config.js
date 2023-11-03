const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
    // 在npm run build 或 yarn build 时 ，生成文件的目录名称（要和baseUrl的生产环境路径一致）（默认dist）
    outputDir: '../webui',
    // 如果你不需要生产环境的 source map，可以将其设置为 false 以加速生产环境构建。
    productionSourceMap: false,
  devServer: {
    host: '0.0.0.0',
      port: 5173,
    historyApiFallback: true,
    allowedHosts: "all"
  }
})
