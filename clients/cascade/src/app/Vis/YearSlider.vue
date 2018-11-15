<template>
  <div class="year-slider-component">
  </div>
</template>

<script>
import * as d3 from '../../../static/d3.v5.min.js'
import { sliderHorizontal } from './d3-time-slider.js'

export default {
  name: 'year-slider',

  props: {
    years: Array
  },

  data() {
    return {
      sliderYear: null,
      margin: { left: 20, right: 20, top: 20, bottom: 10 },
      svgWidth: 0,
      svgHeight: 70,
      width: 0,
      svg: null,
      g: null,
    }
  },

  watch: {
    years(newData) {
      if (newData.length > 0) {
        this.sliderYear = this.years[this.years.length - 1]
        this.draw()
      }
    },
    sliderYear(newData) {
      this.$emit('yearChanged', newData)
    }
  },

  created() {
  },

  mounted() {
    window.addEventListener('resize', this.handleResize)
    this.setupWidthHeight()
    this.setup()
  },

  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
  },

  methods: {
    redraw() {
      this.svg.remove()
      this.setupWidthHeight()
      this.setup()
      this.draw()
    },

    handleResize() {
      this.redraw()
    },

    setupWidthHeight() {
      this.svgWidth = this.$el.offsetWidth
      this.width = this.$el.offsetWidth - this.margin.left - this.margin.right
    },

    setup() {
      this.svg = d3.select(this.$el)
        .append('svg')
        .attr('width', this.svgWidth)
        .attr('height', this.svgHeight)

      this.g = this.svg.append('g')
        .attr('transform', `translate(${this.margin.left},${this.margin.top})`)
    },

    draw() {
      const years = this.years.map(d => new Date(d, 10, 3))
      const defaultYear = new Date(this.sliderYear, 10, 3)

      const slider = sliderHorizontal()
        .min(d3.min(years))
        .max(d3.max(years))
        .step(1000 * 60 * 60 * 24 * 365)
        .width(this.width)
        .tickFormat(d3.timeFormat('%Y'))
        .tickValues(years)
        .default(defaultYear)
        .on('onchange', val => {
          this.sliderYear = parseInt(d3.timeFormat('%Y')(val))
        });

      this.g.call(slider)
    }
  }
}
</script>
