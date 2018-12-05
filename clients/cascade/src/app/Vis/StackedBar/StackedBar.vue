<template>
  <div class="stacked-bar">
    <table class="legend-table table is-narrow" v-if="legendDisplay">
      <tbody>
        <tr v-for="key in legendKeys" :key="key">
          <td>
            <span 
              class="legend-colour" 
              :style="{ 'background-color': legendColour[key] }">
            </span>
          </td>
          <td>{{ getLabel(key)}}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import * as d3 from '../../../../static/d3.v5.min.js'

export default {
  name: 'stacked-bar',

  props: {
    stackedBarData: Object,
    year: Number,
    h: Number,
    yAxisTitle: String,
    colourScheme: Array,
    legendDisplay: Boolean,
    marginObj: Object,
  },

  data() {
    return {
      id: null,
      keys: [],
      results: [],
      dict: {},
      currentData: {},
      svgWidth: 0,
      svgHeight: this.h || 300,
      colours: d3.schemeCategory10,
      width: 0,
      height: 0,
      margin: { left: 60, right: 60, top: 10, bottom: 20 },
      t: d3.transition().duration(0),
      svg: null,
      g: null,
      x: null,
      y: null,
      z: null, // stacked colours
      area: null,
      xAxis: null,
      yAxis: null,
      xAxisGroup: null,
      yAxisGroup: null,
      yAxisLabel: null,
      legendKeys: [],
      legend: {},
      legendColour: {},
    }
  },

  watch: {
    stackedBarData(newData) {
      this.updateOptions(newData)
    },
    keys(newData) {
      this.setupLegend(newData)
    },
    year() {
      this.update()
    },
    colourScheme(newData) {
      this.colours = newData
      this.setupLegend(this.keys)
      this.update()
    }
  },

  created() {
    this.id = this._uid
    this.setupLegend(this.keys)

    if (this.colourScheme && this.colourScheme.length > 0) {
      this.colours = this.colourScheme
    }

    if (this.marginObj) {
      this.margin = this.marginObj
    }
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
    setupLegend(keys) {
      // create the legend
      keys.forEach((key, i) => {
        this.legend[key] = 0
        this.legendColour[key] = this.colours[i]
      })

      this.legendKeys = keys.slice()
      this.legendKeys.reverse()
    },

    getUniqueName(keyString, prependString) {
      const newKey = keyString ? keyString.replace(/ +/g, '').toLowerCase() : ''
      return `${prependString}-${this.id}-${newKey}`
    },

    getLabel(key) {
      return this.dict ? this.dict[key] : key
    },

    redraw() {
      // redraw
      this.svg.remove()
      this.setupWidthHeight()
      this.setup()
      this.update()
    },

    updateOptions(data) {
      const updated = data
      this.keys = updated.keys.reverse()
      this.dict = updated.dict
      this.results = updated.results
      this.currentData = updated.model
      this.update()
    },

    handleResize() {
      this.redraw()
    },

    setupWidthHeight() {
      const chartWidth = this.$el.offsetWidth - 190
      this.svgWidth = chartWidth
      this.width = chartWidth - this.margin.left - this.margin.right
      this.height = this.svgHeight - this.margin.top - this.margin.bottom
    },

    setup() {
      this.x = d3.scaleBand()
        .range([0, this.width])
        .paddingInner(0.6)
        .paddingOuter(0.5)

      this.y = d3.scaleLinear()
      this.z = d3.scaleOrdinal()
        .range(this.colours)
        
      this.xAxis = d3.axisBottom(this.x)
      this.yAxis = d3.axisLeft(this.y)
        .tickFormat(d => {
          if (d < 1000 && d > 99) {
            return `${d/1000}k`;
          } else {
            return d3.format('~s')(d);
          }
        })
      
      this.svg = d3.select(this.$el)
        .append('svg')
        .attr('width', this.svgWidth)
        .attr('height', this.svgHeight)
        .style('background-color', '#fff')

      
      this.g = this.svg.append('g')
        .attr('transform', `translate(${this.margin.left},${this.margin.top})`)
      
      this.xAxisGroup = this.g.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0, ${this.height})`)
      
      this.yAxisGroup = this.g.append('g')
        .attr('class', 'y-axis')

      // x axis label
      this.g.append('text')
        .attr('class', 'x-label')
        .attr('x', this.width/2)
        .attr('y', this.height + 40)
        .attr('font-size', '20px')
        .attr('text-anchor', 'middle')
      
      // y axis label
      this.yAxisLabel = this.g.append('text')
        .attr('class', 'y-label')
        .attr('x', -(this.height/2))
        .attr('y', -45)
        .attr('transform', 'rotate(-90)')
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '13px')
        .style('font-weight', 'bold')
        .style('text-anchor', 'middle')
    },

    update() {
      const data = this.currentData[this.year]
      const keys = this.keys.slice(0)
      const keyColours = this.colours.slice(0)
      const stack = d3.stack()

      stack.keys(keys)

      // sum total
      data.forEach((d) => {
        let total = 0
        keys.forEach((k) => {
          total += d[k]
        })
        d._total = total
      })

      // axis and domain setup
      this.x.domain(data.map(r => r.stage))
      this.y.domain([0, d3.max(data, r => r._total )]).range([this.height, 0]).nice()
      this.z = d3.scaleOrdinal().range(this.colours).domain(keys)
      
      this.xAxisGroup
        .call(this.xAxis)
      this.yAxisGroup
        .call(this.yAxis)

      this.yAxisLabel
        .text(`${this.yAxisTitle} (${this.year})`)

      // Remove 
      this.g.select('.stacked-bars').remove()
      this.g.select('.stacked-bar-texts').remove()
      this.g.select('.legend').remove()

      // legend
      const legend = this.g.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${this.width - this.margin.left - 20}, 0)`)
        .style('opacity', 0)
            
      const legendItem = legend
        .selectAll('.legend')
        .data(keys.reverse())
        .enter().append('g')
        .attr('class', 'legend-item')
      
      legendItem.append('rect')
        .attr('x', 0)
        .attr('y', (d, i) => 20 * i)
        .attr('width', 15)
        .attr('height', 15)
        .style('fill', d => this.legendColour[d])
      
      legendItem.append('text')
        .attr('x', 20)
        .attr('y', (d, i) => 20 * i + 12)
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '12px')
        .style('fill', '#00267a')
        .text(d => this.getLabel(d))

      // Stacked Bar
      const stackedBar = this.g.append('g')
        .attr('class', 'stacked-bars')
        .selectAll('.stacked-bars')
        .data(stack(data))
      
      const stackedFillBar = stackedBar.enter().append('g')
        .attr('class', d => `fill-bar ${this.getUniqueName(d.key, 'bar')}`)
        .attr('fill', d => this.z(d.key))

      const rects = stackedFillBar.selectAll('rect')
        .data((d) => {
          d.forEach((k) => {
            k.key = d.key
          })
          return d
        })

      rects.enter().append('rect')
        .attr('x', d => this.x(d.data.stage))
        .attr('y', d => this.y(d[1]))
        .attr('height', d => this.y(d[0]) - this.y(d[1]))
        .attr('width', this.x.bandwidth)
        .style('fillOpacity', 0)
        .on('mouseover', (d) => {
          const barClass = this.getUniqueName(d.key, 'bar')
          const textClass = this.getUniqueName(d.key, 'cat-text')
          d3.selectAll(`.fill-bar:not(.${barClass})`)
            .style('opacity', 0.3)
          d3.selectAll(`.${textClass}`)
            .style('display', d => d[0] === 0 && d[1] === 0 ? 'none' : 'block')
        })
        .on('mouseout', (d) => {
          const textClass = this.getUniqueName(d.key, 'cat-text')
          d3.selectAll('.fill-bar')
            .style('opacity', 1)
          d3.selectAll(`.cat-text`)
            .style('display', 'none')          
          d3.selectAll(`.${textClass}`)
            .style('display', 'none')
        })
        .merge(rects)
        .transition(this.t)
          .attr('fillOpacity', 1)

      const stackedBarTexts = this.g.append('g')
        .attr('class', 'stacked-bar-texts')
        .selectAll('.stacked-bar-texts')
        .data(stack(data))

      const categoryText = stackedBarTexts.enter().append('g').selectAll('text')
        .data((d) => {
          d.forEach((k) => {
            k.key = d.key
          })
          return d
        })
      
      categoryText.enter().append('text')
        .attr('class', d => `cat-text ${this.getUniqueName(d.key, 'cat-text')}`)
        .attr('x', d => this.x(d.data.stage) + this.x.bandwidth() / 2)
        .attr('y', d => this.y(d[1]) - 2)
        .style('text-anchor', 'middle')
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .style('display', 'none')
        .text(d => `${d3.format(',.0f')(d[1] - d[0])}`)

      this.$emit('chartUpdated', this.svg, this.width, this.height);
    }
  }
}
</script>

<style lang="scss" scoped>

.stacked-bar {
  position: relative;
  display: flex;
  flex-direction: row-reverse;
}

.legend-colour {
  display: block;
  width: 15px;
  height: 15px;
}

.legend-table.table {
  border: none;
  width: 160px;
  border-collapse: collapse;

  td, th {
    padding: 3px 2px 2px;
    text-align: left;
    border: none;
    font-size: 11px;
    font-weight: normal;
  }

  thead > tr > th,
  tbody > tr > td {
    background: transparent;
    color: #000;
    line-height: 1;
  }
}
</style>
