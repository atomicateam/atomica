<template>
  <div class="save-options">
    <button class="chart-save-btn" @click="save">Export graph</button>
  </div>
</template>

<script>
import { getSVGString, svgString2Image } from './svg-to-png'

export default {
  name: 'save-options',

  props: {
    filename: String,
    chartSvg: Object,
    chartWidth: Number,
    chartHeight: Number
  },

  methods: {
    save() {
      const legend = this.chartSvg.node().querySelector('.legend')
      legend.style.opacity = 1

      const svgString = getSVGString(this.chartSvg.node())
      svgString2Image( svgString, 2*this.chartWidth, 2*this.chartHeight, 'png', save )

      const filename = this.filename

      function save (dataBlob, filesize) {
        saveAs (dataBlob, `${filename}.png`)
        legend.style.opacity = 0
      }
    },
  }
}
</script>

<style lang="scss" scoped>
.chart-save-btn {
  border: none;
  background: #00267a;
  color: #fff;
  padding: 4px 8px;
  font-size: 16px;
  border-radius: 3px;
  cursor: pointer;
}
</style>
