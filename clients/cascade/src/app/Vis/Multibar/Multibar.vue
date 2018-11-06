<template>
  <div class="multi-bar-cascade">
    <!-- Arrow def -->
    <svg width="0" height="0">
      <defs>
        <marker id="arrow" markerWidth="7" markerHeight="5" refX="0" refY="2.5" orient="auto">
        <polygon points="0 0, 7 2.5, 0 5" />
    </marker>
      </defs>
    </svg>

    <table class="legend-table table is-narrow">
      <tbody class="scenarios">
        <tr>
          <td></td>
          <td>Scenarios</td>                      
        </tr>
        <tr v-for="key in legendKeys" :key="key">
          <td>
            <span 
              class="legend-colour" 
              :style="{ 'background-color': legendColour[key] }">
            </span>
          </td>
          <td>{{key}}</td>
        </tr>
      </tbody>

      <tbody class="subpopulation">
        <tr>
          <td></td>
          <td>Subpopulation</td>                      
        </tr>
        <tr v-for="category in categories" :key="category">
          <td>
            <div class="check-box grouped-population-checkbox">
              <input type="checkbox" :id="`${id}-${category}`" :value="category" v-model="selectedCategories">
              <label :for="`${id}-${category}`">
                <span class="legend-colour" ></span>
              </label>
            </div>
          </td>
          <td>{{ getLabel(category) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import * as d3 from '../../../../static/d3.v5.min.js' // CK: Warning, replace with import * as d3 from 'd3'
import cascadeStep from '../cascade-step'
import { transformMultiData } from '../data-transform'

export default {
  name: 'multi-bar-cascade',

  props: {
    multiData: Object,
    h: Number,
    yAxisTitle: String,
    colourScheme: Array,
    year: Number,
  },

  data() {
    return {
      id: null,
      currentData: {},
      keys: [],
      categories: [],
      selectedCategories: [],
      dict: {},
      svgWidth: 0,
      svgHeight: this.h || 300,
      width: 0,
      height: 0,
      colours: d3.schemeSet1,
      margin: { left: 75, right: 190, top: 10, bottom: 20 },
      t: d3.transition().duration(0),
      svg: null,
      g: null,
      x1: null,
      x0: null,
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
      legendColour: {},
    }
  },

  watch: {
    multiData(newData) {
      this.updateOptions(newData)
    },
    keys(newData) {
      this.setupLegend(newData)
    },
    categories(newData) {
      this.selectedCategories = newData.slice()
    },
    year() {
      this.update()
    },
    selectedCategories() {
      if (this.year) {
        this.updateOptions(this.multiData)
      }
    },
  },

  created() {
    this.setupLegend(this.keys)
    this.selectedCategories = this.categories.slice()

    if (this.colourScheme && this.colourScheme.length > 0) {
      this.colours = this.colourScheme
    }
  },

  mounted() {
    this.id = this._uid
    window.addEventListener('resize', this.handleResize)

    this.setupWidthHeight()
    this.setup()
  },

  beforeDestroy: function () {
    window.removeEventListener('resize', this.handleResize)
  },

  methods: {
    setupLegend(keys) {
      // create the legend
      keys.forEach((key, i) => {
        this.legendColour[key] = this.colours[i]
      })

      this.legendKeys = keys.slice()
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
      this.keys = updated.results
      this.categories = updated.keys
      this.dict = updated.dict

      this.currentData = updated.data
      this.update()
    },

    handleResize() {
      this.redraw()
    },

    setupWidthHeight() {
      this.svgWidth = this.$el.offsetWidth
      this.width = this.$el.offsetWidth - this.margin.left - this.margin.right
      this.height = this.svgHeight - this.margin.top - this.margin.bottom
    },

    getUniqueName(keyString, prependString) {
      return `${prependString}-${this.keys.indexOf(keyString)}`
    },

    getLabel(category) {
      return this.dict ? this.dict[category] : category
    },

    areaData(data) {
      return this.keys.map(function(key) {
        const areaData = { key }
        areaData.stages = []
        
        data.forEach(d => {
          areaData.stages.push({
            key,
            stage: d.stage,
            value: d[key]
          })
        })

        return areaData
      })
    },
 
    setup() {
      this.x0 = d3.scaleBand()
        .rangeRound([0, this.width])
        .paddingInner(0.2)
        .paddingOuter(0.3)

      this.x1 = d3.scaleBand()
        .padding(0.1)

      this.y = d3.scaleLinear()
      this.z = d3.scaleOrdinal()
        .range(this.colours)
        
      this.xAxis = d3.axisBottom(this.x0)
      this.yAxis = d3.axisLeft(this.y)
        .tickFormat(d => {
          if (d < 1000 && d > 99) {
            return `${d/1000}k`
          } else {
            return d3.format('~s')(d)
          }
        })

      this.svg = d3.select(this.$el)
        .append('svg')
        .attr('width', this.svgWidth)
        .attr('height', this.svgHeight)
      
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
        .style('font-size', '13px')
        .style('font-weight', 'bold')
        .style('text-anchor', 'middle')
    },

    update() {
      const data = transformMultiData(this.keys, this.multiData, this.year, this.selectedCategories)
      const x1Padding = this.keys.length <= 1 ? 0.4 : 0.1
      
      // axis and domain setup
      this.x0.domain(data.map(r => r.stage))
      this.x1.domain(this.keys).rangeRound([0, this.x0.bandwidth()]).padding(x1Padding)
      this.y.domain([0, d3.max(data, r => r.highest )]).range([this.height, 0]).nice()
      this.z.domain(this.keys)
      
      this.xAxisGroup
        .call(this.xAxis)
      this.yAxisGroup
        .call(this.yAxis)

      this.yAxisLabel
        .text(this.yAxisTitle)

      // Setup area curve and drawing data
      const area = d3.area()
        .curve(d => cascadeStep(d, this.x1.bandwidth()))
        .x0(d => this.x0(d.stage) + this.x1(d.key))
        .y0(() => this.y(0))
        .y1(d => this.y(d.value))
      
      // Remove existing vis for redraw
      this.g.select('.multi-bars').remove()
      this.g.select('.multi-areas').remove()
      this.g.select('.multi-bar-text').remove()

      // Cascade Area
      const multiAreasGroup = this.g.append('g').attr('class', 'multi-areas')
      const multiAreas = multiAreasGroup
        .selectAll('.layer')
        .data(this.areaData(data))
      
      multiAreas
        .enter()
          .append('g')
          .attr('class', 'layer')
          .append('path')
            .attr('class', d => `area ${this.getUniqueName(d.key, 'area')}`)
            .style('opacity', 0)
            .style('fill', d => this.z(d.key))
            .attr('d', d => area(d.stages))
      
      // Bars
      const multiBarsGroup = this.g.append('g')
        .attr('class', 'multi-bars')
        .selectAll('.multi-bars')
        .data(data)

      const multiBars = multiBarsGroup.enter().append('g')
        .attr('transform', d => 'translate(' + this.x0(d.stage) + ',0)')
        .selectAll('rect')
        .data(d => this.keys.map((key) => {
          return {
            key: key,
            value: d[key]
          }
        }))
      
      multiBars.enter().append('rect')
        .attr('x', d => this.x1(d.key))
        .attr('y', d => this.y(d.value))
        .attr('width', this.x1.bandwidth())
        .attr('height', d => this.height - this.y(d.value))
        .attr('fill', d => this.z(d.key))
        .attr('fillOpacity', 0)
        .attr('class', d => `rect ${this.getUniqueName(d.key, 'rect')}`)
        // .on('mousedown', d => {
        //   this.$emit('click', d)
        // })
        .on('mouseover', d => {
          this.$emit('mouseover', d)

          const areaClass = this.getUniqueName(d.key, 'area')
          const rectClass = this.getUniqueName(d.key, 'rect')
          const textClass = this.getUniqueName(d.key, 'cat-text')

          d3.selectAll(`.${areaClass}`).transition()
            .style('opacity', 0.4)
          d3.selectAll(`.multi-bars rect:not(.${rectClass})`).transition()
            .style('opacity', .1)
          d3.selectAll(`.${textClass}`)
            .style('display', 'block')

        })
        .on('mouseout', d => {
          this.$emit('mouseout', d)

          const areaClass = this.getUniqueName(d.key, 'area')
          const textClass = this.getUniqueName(d.key, 'cat-text')

          d3.selectAll(`.${areaClass}`).transition()
            .style('opacity', 0)
          d3.selectAll('.rect').transition()
            .style('opacity', 1)
          d3.selectAll(`.${textClass}`)
            .style('display', 'none')

        })
        .merge(multiBars)
        .transition(this.t)
          .attr('opacity', 1)
      
      // Text
      const lastDataIndex = data.length - 1
      const multiBarTexts = this.g.append('g')
        .attr('class', 'multi-bar-text')
        .selectAll('.multi-bar-text')
        .data(this.areaData(data))

      const categoryText = multiBarTexts.enter().append('g')
        .attr('class', d => `cat-text ${this.getUniqueName(d.key, 'cat-text')}`)
        .style('display', 'none')
        .selectAll('text')
        .data((d) => {
          const lastIndex = d.stages.length - 1
          const firstStageValue = d.stages[0].value
          // add key
          d.stages.forEach((k, j) => {
            k.percent = k.value / firstStageValue * 100

            if (j === lastIndex) {
              k.conversion = 0
            } else {
              k.conversion = d.stages[j+1].value / d.stages[j].value * 100
            }
          })
          return d.stages
        })
      
      categoryText.enter().append('text')
        .attr('x', (d) => this.x1(d.key) + this.x0(d.stage) + 2)
        .attr('y', (d) => this.y(d.value) - 2)
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .text(d => `${d3.format(',.0f')(d.percent)}%`)

      // Arrow
      categoryText.enter()
        .append('line')
        .style('stroke', '#00267a')
        .style('stroke-width', 2)
        .style('stroke-dasharray', '10,3')
        .style('marker-end','url(#arrow)')
        .style('display', (d, i) => lastDataIndex === i ? 'none' : 'block')
        .attr('x1', d => this.x1(d.key) + this.x0(d.stage) + this.x0.bandwidth() / 2)
        .attr('x2', d => this.x1(d.key) + this.x0(d.stage) + this.x0.bandwidth())
        .attr('y1', () => this.y(0) - 9)
        .attr('y2', () => this.y(0) - 9)
      
      categoryText.enter()
        .append('text')
        .attr('x', d => this.x1(d.key) + this.x0(d.stage) + this.x0.bandwidth() / 2)
        .attr('y', () => this.y(0) - 15)
        .attr('text-anchor', 'start')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .text((d, i) => { return lastDataIndex === i ? '' : `${d3.format('.1f')(d.conversion)}%` })

    }
  }
}
</script>

<style lang="scss" scoped>
.multi-bar-cascade {
  position: relative;
}

.legend-colour {
  display: block;
  width: 15px;
  height: 15px;
}

.legend-table.table {
  border: none;
  position: absolute;
  right: 0;
  top: 0;
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

  > tbody + tbody {
    border: none;
  }

  .scenarios tr:first-child td,
  .subpopulation tr:first-child td {
    padding-top: 15px;
    padding-bottom: 5px;
    border-bottom: 1px solid #ddd;
    font-weight: bold;
  }
   .scenarios tr:first-child td {
     padding-top: 0;
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
      border-left: 1px solid #999;
      border-bottom: 1px solid #999;
      
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

