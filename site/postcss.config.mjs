import { postcssIsolateStyles } from 'vitepress'

// Components embedded in Markdown carry class `vp-raw`, so the doc typography
// (list margins, link colors, heading borders) stays out of them.
export default {
  plugins: [postcssIsolateStyles({ includeFiles: [/vp-doc\.css/] })],
}
