<template>
  <div class="stacked-cascade">
    <div class="selections">
      <select class="select" v-model="result">
        <option v-for="option in resultsOptions" :key="option" :value="option">
          {{ option }}
        </option>
      </select>
      <select class="select" v-model="year">
        <option v-for="option in yearOptions" :key="option" :value="option">
          {{ option }}
        </option>
      </select>
    </div>

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
import * as d3 from 'd3'
import { transformDataForChartRender, transformCascadeData } from '@/modules/data-transform'
import cascadeStep from '@/modules/cascade-step'

export default {
  name: 'stacked-cascade',

  props: {
    cascadeData: Object,
    h: Number,
    yAxisTitle: String,
    colourScheme: Array,
    legendDisplay: Boolean,
    marginObj: Object,
  },

  data() {
    return {
      keys: [],
      dict: {},
      result: null,
      resultsOptions: [],
      year: null,
      yearOptions: [],
      currentData: {},
      svgWidth: 0,
      svgHeight: this.h || 300,
      colours: d3.schemeDark2,
      width: 0,
      height: 0,
      margin: { left: 75, right: 40, top: 10, bottom: 20 },
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
    result(newValue) {
      this.update()
    },
    year(newValue) {
      this.update()
    }
  },

  created() {
    if (this.colourScheme && this.colourScheme.length > 0) {
      this.colours = this.colourScheme
    }
    this.setupLegend(this.keys)
    if (this.marginObj) {
      this.margin = this.marginObj
    }
  },

  mounted() {
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
        this.legend[key] = 0
        this.legendColour[key] = this.colours[i]
      })

      this.legendKeys = keys.slice()
      // reverse the order of the keys so it is in line with the stacked chart
      this.legendKeys.reverse()
    },

    getLabel(key) {
      return this.dict ? this.dict[key] : key
    },

    redraw() {
      // redraw
      this.svg.remove()
      this.setupWidthHeight()
      this.setup()
      this.updateOptions(this.cascadeData)
    },

    updateOptions(data) {
      const updated = transformCascadeData(data)
      this.keys = updated.keys
      this.dict = updated.dict

      this.resultsOptions = updated.results
      this.result = updated.results[0]

      this.yearOptions = updated.years
      this.year = updated.years[0]

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
      const data = transformDataForChartRender(this.keys, this.currentData[this.result][this.year])

      const keys = this.keys
      const stack = d3.stack()

      stack.keys(keys)

      // axis and domain setup
      this.x.domain(data.map(r => r.stage))
      this.y.domain([0, d3.max(data, r => r._total )]).range([this.height, 0]).nice()

      // this.y.domain([0, 90000]).range([this.height, 0])
      this.z.domain(keys)
      
      this.xAxisGroup
        .call(this.xAxis)
      this.yAxisGroup
        .call(this.yAxis)

      this.yAxisLabel
        .text(this.yAxisTitle)

      const area = d3.area()
        .curve(cascadeStep)
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
            .attr('class', (d) => `area ${d.key}-area`)
            .style('opacity', 0)
            .style('fill', (d) => this.z(d.key))
            .attr('d', area)
          // .transition(d3.transition().duration(100))
            .style('opacity', 0.3)
        
      const stackedBar = this.g.append('g')
        .attr('class', 'stacked-bars')
        .selectAll('.stacked-bars')
        .data(stack(data))

      const stackedFillBar = stackedBar.enter().append('g')
        .attr('class', (d) => `fill-bar ${d.key}`)
        .attr('fill', (d) => this.z(d.key))

      const rects = stackedFillBar.selectAll('rect')
        .data((d) => {
          d.forEach((k) => {
            k.key = d.key
          })
          return d
        })

      rects.enter().append('rect')
        .attr('x', (d) => this.x(d.data.stage))
        .attr('y', (d) => { return this.y(d[1]) })
        .attr('height', (d) => { return this.y(d[0]) - this.y(d[1]) })
        .attr('width', this.x.bandwidth)
        .style('fillOpacity', 0)
        .on('mouseover', (d) => {
          this.keys.forEach(key => {
            this.legend[key] = d.data[key]
          })

          d3.selectAll('.fill-bar')
            .style('opacity', 0.5)
          d3.selectAll('.area')
            .style('opacity', 0)
          d3.selectAll('.stage-total-texts')
            .style('opacity', 0)
          d3.selectAll(`.${d.key}`)
            .style('opacity', 1)
          d3.selectAll(`.${d.key}-cat-text`)
            .style('display', 'block')
          d3.selectAll(`.${d.key}-area`)
            .style('opacity', 0.5)

          this.showLegend = true
        })
        .on('mouseout', (d) => {
          d3.selectAll('.fill-bar')
            .style('opacity', 1)
          d3.selectAll(`.cat-text`)
            .style('display', 'none')
          d3.selectAll(`.${d.key}-cat-text`)
            .style('display', 'none')
          d3.selectAll('.area')
            .style('opacity', 0.3)
          d3.selectAll('.stage-total-texts')
            .style('opacity', 1)
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

      stageTotal
        .enter().append('text')
        .attr('x', (d) => this.x(d.stage) + 2)
        .attr('y', (d) => this.y(d._total) - 2)
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .text(d => d3.format(',.0f')(d._total))
      
      stageTotal
        .enter().append('text')
        .attr('x', (d) => this.x(d.stage) + this.x.bandwidth(d.stage) + 2)
        .attr('y', (d) => this.y(d._total))
        .style('font-size', '10px')
        .style('font-weight', 'bold')
        .style('fill', '#C74523')
        .text((d, i) => { return lastDataIndex === i ? '' : `Loss: ${d3.format(',.0f')(d.loss)}` })
      
      stageTotal
        .enter().append('text')
        .attr('x', (d) => this.x(d.stage) + this.x.bandwidth(d.stage) + this.x.bandwidth(d.stage)/2)
        .attr('y', () => this.y(0) + 9)
        .attr('text-anchor', 'middle')
        .style('font-size', '9px')
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
        .attr('class', (d) => `cat-text ${d.key}-cat-text`)
        .attr('x', (d) => this.x(d.data.stage) + 2)
        .attr('y', (d) => this.y(d[1]) - 2)
        // .attr('y', (d) => { return (this.y(d[1]) - this.y(d[0])) / 2 + this.y(d[0]) })
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .style('display', 'none')
        .text((d) => { return `${d3.format(',.0f')(d[1] - d[0])}` })
      
      categoryText.enter().append('text')
        .attr('class', (d) => `cat-text ${d.key}-cat-text`)
        .attr('x', (d) => this.x(d.data.stage) + this.x.bandwidth(d.data.stage) + 2)
        .attr('y', (d) => this.y(d[1]))
        .style('font-size', '10px')
        .style('font-weight', 'bold')
        .style('fill', '#C74523')
        .style('display', 'none')
        .text((d, i) => { return lastDataIndex === i ? '' : `Loss: ${d3.format(',.0f')(d.loss)}` })

      categoryText.enter().append('text')
        .attr('class', (d) => `cat-text ${d.key}-cat-text`)
        .attr('x', (d) => this.x(d.data.stage) + this.x.bandwidth(d.data.stage) + this.x.bandwidth(d.data.stage)/2)
        // .attr('y', d => this.y(d[0]) - 2)
        .attr('y', () => this.y(0) + 9)
        .attr('text-anchor', 'middle')
        .style('font-size', '9px')
        .style('font-weight', 'bold')
        .style('fill', '#00267a')
        .style('display', 'none')
        .text((d, i) => { return lastDataIndex === i ? '' : `${d3.format('.1f')(d.conversion)}%` })
    }
  }
}
</script>

<style lang="scss" scoped>
.stacked-cascade {
  position: relative;
}
.tooltip {	
  position: absolute;			
  width: 100px;					
  height: 30px;					
  padding: 2px 4px;				
  font: 12px sans-serif;		
  background: #fff;	
  border: 1px solid #eee;		
  border-radius: 2px;			
  pointer-events: none;			
}
.legend-colour {
  display: block;
  width: 15px;
  height: 15px;
}
.legend-table {
  position: absolute;
  right: 2rem;
  top: 10px;
  font-size: 11px;
}
.legend-table.table td {
  padding: 3px 5px 2px;
}
.selections {
  text-align: center;

  .select {
    font-size: 1rem;
    margin-right: 1rem;
  }
}
</style>

