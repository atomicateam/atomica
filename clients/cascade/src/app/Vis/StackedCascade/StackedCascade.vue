<template>
  <div class="stacked-cascade">
    <table class="legend-table table is-narrow" v-if="legendDisplay">
      <thead>
        <tr>
          <th>
            <div class="check-box grouped-population-checkbox">
              <input type="checkbox" :id="`${id}-grouped-population-checkbox`" v-model="groupPopulations">
              <label :for="`${id}-grouped-population-checkbox`">
                <span 
                  class="legend-colour"
                >
                </span>
              </label>
            </div>
          </th>
          <th>Group Populations</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="key in legendKeys" :key="key">
          <td>
            <div class="check-box">
              <input type="checkbox" :id="`${id}-${key}`" :value="key" v-model="selectedKeys">
              <label :for="`${id}-${key}`">
                <span 
                  class="legend-colour" 
                  :style="{ 'background-color': groupPopulations ? '#00267a' : legendColour[key] }">
                </span>
              </label>
            </div>
          </td>
          <td>{{ getLabel(key)}}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import * as d3 from '../../../../static/d3.v5.min.js'
import { transformDataForChartRender } from '../data-transform'
import cascadeStep from '../cascade-step'

const TOTAL = '_total'
const TOTAL_COLOUR = '#00267a'
const DATA_TOTAL_COLOUR = '#ff7f0e'

export default {
  name: 'stacked-cascade',

  props: {
    cascadeData: Object,
    year: Number,
    scenario: String,
    h: Number,
    yAxisTitle: String,
    colourScheme: Array,
    totalColour: String,
    legendDisplay: Boolean,
    marginObj: Object,
    defaultTotal: Boolean
  },

  data() {
    return {
      id: null,
      keys: [],
      selectedKeys: [],
      groupPopulations: this.defaultTotal || false,
      dict: {},
      currentData: {},
      svgWidth: 0,
      svgHeight: this.h || 300,
      colours: d3.schemeCategory10,
      tColour: this.totalColour || TOTAL_COLOUR,
      width: 0,
      height: 0,
      margin: { left: 60, right: 30, top: 10, bottom: 20 },
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
      tooltip: null,
      legendKeys: [],
      legend: {},
      legendColour: {},
      showLegend: false,
    }
  },

  watch: {
    cascadeData(newData) {
      this.updateOptions(newData)
    },
    keys(newData) {
      this.setupLegend(newData)
    },
    selectedKeys() {
      if (this.year) {
        this.updateOptions(this.cascadeData)
      }
    },
    groupPopulations() {
      this.update()
    },
    year() {
      this.update()
    },
    scenario() {
      this.update()
    },
    colourScheme(newData) {
      this.colours = newData
      this.setupLegend(this.keys)
      this.update()
    }
  },

  created() {
    this.setupLegend(this.keys)

    if (this.colourScheme && this.colourScheme.length > 0) {
      this.colours = this.colourScheme
    }

    if (this.marginObj) {
      this.margin = this.marginObj
    }
  },

  mounted() {
    this.id = this._uid

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

      this.legendColour[TOTAL] = this.tColour

      this.legendKeys = keys.slice()
      this.selectedKeys = keys.slice()
      // reverse the order of the keys so it is in line with the stacked chart
      this.legendKeys.reverse()
    },

    getUniqueName(keyString, prependString) {
      return `${prependString}-${this.keys.indexOf(keyString)}`
    },

    getLabel(key) {
      return this.dict ? this.dict[key] : key
    },

    getKeysInOrder(allKeys, selectedKeys) {
      let keys = []

      if (selectedKeys[0] === TOTAL) {
        keys = selectedKeys
      } else {
        allKeys.forEach(key => {
          const find = selectedKeys.find(selectedKey => key === selectedKey)
          if (find) {
            keys.push(find)
          }
        })
      }
      
      return keys
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
      this.keys = updated.keys
      this.dict = updated.dict

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
        .paddingInner(0.5)
        .paddingOuter(0.2)

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

      // arrow def
      this.svg.append('defs')
        .append('marker')
          .attr('id', 'arrow')
          .attr('markerWidth', '7')
          .attr('markerHeight', '5')
          .attr('refX', '0')
          .attr('refY', '2.5')
          .attr('orient', 'auto')
        .append('polygon')
          .attr('points', '0 0, 7 2.5, 0 5')
      
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
        .attr('y', -50)
        .attr('transform', 'rotate(-90)')
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '13px')
        .style('font-weight', 'bold')
        .style('text-anchor', 'middle')
    },

    update() {
      const data = transformDataForChartRender(this.selectedKeys, this.currentData[this.scenario][this.year])
      
      const keys = this.getKeysInOrder(this.keys, this.selectedKeys)
      const keyColours = keys.map(key => this.groupPopulations ? this.tColour : this.legendColour[key])
      const stack = d3.stack()

      stack.keys(keys)

      // axis and domain setup
      this.x.domain(data.map(r => r.stage))
      this.y.domain([0, d3.max(data, r => r._total )]).range([this.height, 0]).nice()
      this.z = d3.scaleOrdinal().range(keyColours).domain(keys)
      
      this.xAxisGroup
        .call(this.xAxis)
      this.yAxisGroup
        .call(this.yAxis)

      this.yAxisLabel
        .text(this.yAxisTitle)

      const area = d3.area()
        .curve((d) => cascadeStep(d, this.x.bandwidth()))
        .x0((d) => { return this.x(d.data.stage); })
        .y0((d) => this.y(d[0]))
        .y1((d) => this.y(d[1]))

      // Remove 
      this.g.select('.stacked-areas').remove()
      this.g.select('.stacked-bars').remove()
      this.g.select('.stage-total-texts').remove()
      this.g.select('.stacked-bar-texts').remove()

      // DATA JOIN
      const stackedCascadeArea = this.g.append('g')
        .attr('class', 'stacked-areas')
        
      stackedCascadeArea.selectAll('.layer')
        .data(stack(data))
        .enter()
          .append('g')
          .attr('class', 'layer')
          .append('path')
            .attr('class', d => `area ${this.getUniqueName(d.key, 'area')}`)
            .style('opacity', 0)
            .style('fill', d => this.z(d.key))
            .attr('d', area)
            .style('opacity', 0.3)
        
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
          this.keys.forEach(key => {
            this.legend[key] = d.data[key]
          })

          if (!this.groupPopulations) {
            const areaClass = this.getUniqueName(d.key, 'area')
            const barClass = this.getUniqueName(d.key, 'bar')
            const textClass = this.getUniqueName(d.key, 'cat-text')

            d3.selectAll('.area')
              .style('opacity', 0)
            d3.selectAll('.stage-total-texts')
              .style('opacity', 0)
            d3.selectAll(`.fill-bar:not(.${barClass})`)
              .style('opacity', 0.5)
            d3.selectAll(`.${textClass}`)
              .style('display', 'block')
            d3.selectAll(`.${areaClass}`)
              .style('opacity', 0.5)
          }
          this.showLegend = true
        })
        .on('mouseout', (d) => {

          if (!this.groupPopulations) {
            const textClass = this.getUniqueName(d.key, 'cat-text')

            d3.selectAll('.fill-bar')
              .style('opacity', 1)
            d3.selectAll(`.cat-text`)
              .style('display', 'none')
            d3.selectAll(`.${textClass}`)
              .style('display', 'none')
            d3.selectAll('.area')
              .style('opacity', 0.3)
            d3.selectAll('.stage-total-texts')
              .style('opacity', 1)
          }
          
          this.showLegend = false
        })
        .merge(rects)
        .transition(this.t)
          .attr('fillOpacity', 1)
      
      // labels
      const lastDataIndex = data.length - 1
      const stageTotal = this.g.append('g')
        .attr('class', 'stage-total-texts')
        .selectAll('.stage-total-texts')
        .data(data)

      // Data Total circle
      stageTotal
        .enter().append('circle')
        .attr('cx', d => this.x(d.stage) + this.x.bandwidth() / 2)
        .attr('cy', d => this.y(d._dataTotal))
        .attr('r', d => d._dataTotal === 0 ? '0' : '6')
        .style('stroke', DATA_TOTAL_COLOUR)
        .style('stroke-width', '2px')
        .style('fill', '#fff')

      // Total text
      stageTotal
        .enter().append('text')
        .attr('x', d => this.x(d.stage) + 2)
        .attr('y', d => this.y(d._total) - 2)
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .text(d => d3.format(',.0f')(d._total))
      
      // Arrow
      stageTotal.enter()
        .append('line')
        .style('stroke', '#00267a')
        .style('stroke-width', 2)
        .style('stroke-dasharray', '10,3')
        .style('marker-end','url(#arrow)')
        .style('display', (d, i) => lastDataIndex === i ? 'none' : 'block')
        .attr('x1', d => this.x(d.stage) + this.x.bandwidth())
        .attr('x2', d => this.x(d.stage) + this.x.bandwidth() * 1.8)
        .attr('y1', () => this.y(0) + 15)
        .attr('y2', () => this.y(0) + 15)

      stageTotal
        .enter().append('text')
        .attr('x', d => this.x(d.stage) + this.x.bandwidth())
        .attr('y', () => this.y(0) + 12)
        .attr('text-anchor', 'start')
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .text((d, i) => { return lastDataIndex === i ? '' : `${d3.format('.1f')(d.conversion)}%` })

      const stackedBarTexts = this.g.append('g')
        .attr('class', 'stacked-bar-texts')
        .selectAll('.stacked-bar-texts')
        .data(stack(data))

      const categoryText = stackedBarTexts.enter().append('g').selectAll('text')
        .data((d) => {
          const lastIndex = d.length - 1
          // add key
          d.forEach((k, j) => {
            k.key = d.key

            if (j === lastIndex) {
              k.loss = 0
              k.conversion = 0
            } else {
              k.loss = d[j].data[d.key] - d[j+1].data[d.key]
              k.conversion = d[j+1].data[d.key] / d[j].data[d.key] * 100
            }
          })
          return d
        })
      
      categoryText.enter().append('text')
        .attr('class', d => `cat-text ${this.getUniqueName(d.key, 'cat-text')}`)
        .attr('x', d => this.x(d.data.stage) + 2)
        .attr('y', d => this.y(d[1]) - 2)
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .style('display', 'none')
        .text(d => `${d3.format(',.0f')(d[1] - d[0])}`)
            
      categoryText.enter()
        .append('line')
        .style('stroke', '#00267a')
        .style('stroke-width', 2)
        .style('stroke-dasharray', '10,3')
        .style('marker-end','url(#arrow)')
        .style('display', (d, i) => lastDataIndex === i ? 'none' : 'block')
        .attr('x1', d => this.x(d.data.stage) + this.x.bandwidth())
        .attr('x2', d => this.x(d.data.stage) + this.x.bandwidth() * 1.8)
        .attr('y1', () => this.y(0) + 15)
        .attr('y2', () => this.y(0) + 15)

      categoryText.enter().append('text')
        .attr('class', d => `cat-text ${this.getUniqueName(d.key, 'cat-text')}`)
        .attr('x', d => this.x(d.data.stage) + this.x.bandwidth())
        .attr('y', () => this.y(0) + 12)
        .attr('text-anchor', 'start')
        .style('font-family', 'Helvetica, Arial')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .style('display', 'none')
        .text((d, i) => { return lastDataIndex === i ? '' : `${d3.format('.1f')(d.conversion)}%` })

      this.$emit('chartUpdated', this.svg, this.width, this.height)
    }
  }
}
</script>

<style lang="scss" scoped>
.stacked-cascade {
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
  // position: absolute;
  // right: 2rem;
  // top: 0;
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

.check-box {
  width: 15px;
  height: 15px;
  position: relative;

  &.grouped-population-checkbox {
    label::before {
      border: 1px solid #000;
      width: 15px;
      height: 15px;
    }
    
    label::after {
      border-left: 1px solid #000;
      border-bottom: 1px solid #000;
    }
  }
  
  span.legend-colour {
    position: absolute;
    top: 0;
  }

  label {
    display: inline;
    max-width: none;
    font-weight: normal;

    &::before {
      position: absolute;
      
      content: '';
      display: inline-block;   
    }

    &::after {
      position: absolute;
      left: 3px;
      top: 4px;

      content: '';
      display: inline-block;
      height: 4px;
      width: 9px;
      border-left: 1px solid #fff;
      border-bottom: 1px solid #fff;
      
      transform: rotate(-50deg);
    }
  }

  input[type='checkbox'] {
    display: none;
  }

  input[type='checkbox']:focus + label::before {
    outline: rgb(59, 153, 252) auto 5px;
  }

  /* Hide the checkmark by default */
  input[type='checkbox'] + label::after {
      content: none;
  }
  /* Unhide the checkmark on the checked state */
  input[type='checkbox']:checked + label::after {
      content: '';
  }
}
</style>
