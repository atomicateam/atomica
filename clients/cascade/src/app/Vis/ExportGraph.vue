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
    chartSvg: Object,
    chartWidth: Number,
    chartHeight: Number
  },

  methods: {
    save() {
      const svgString = getSVGString(this.chartSvg.node())
      svgString2Image( svgString, 2*this.chartWidth, 2*this.chartHeight, 'png', save )

      function save (dataBlob, filesize) {
        saveAs (dataBlob, 'Figures.png')
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
