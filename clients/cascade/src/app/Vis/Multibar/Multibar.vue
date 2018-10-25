<template>
  <div class="stacked-cascade">
    <table class="legend-table table is-narrow">
      <tbody>
        <tr v-for="key in legendKeys" :key="key">
          <td>
            <span 
              class="legend-colour" 
              :style="{ 'background-color': legendColour[key] }">
            </span>
          </td>
          <td>{{key}}</td>
          <td style="width: 50px; font-weight: bold; text-align: right;">
            <div v-if="showLegend">
              {{legend[key]}}
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import * as d3 from '../../../../static/d3.v5.min.js' // CK: Warning, replace with import * as d3 from 'd3'
import { transformMultiData } from '../data-transform'

export default {
  name: 'multi-bar',

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
      svgWidth: 0,
      svgHeight: this.h || 300,
      width: 0,
      height: 0,
      colours: d3.schemeSet2,
      margin: { left: 75, right: 40, top: 10, bottom: 20 },
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
      legend: {},
      legendColour: {},
      showLegend: false,
    }
  },

  watch: {
    multiData(newData) {
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
    if (this.colourScheme && this.colourScheme.length > 0) {
      this.colours = this.colourScheme
    }

    this.setupLegend(this.keys)
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
        this.legend[key] = 0
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
      this.x0 = d3.scaleBand()
        .rangeRound([0, this.width])
        .paddingInner(0.2)
        .paddingOuter(0.3)

      this.x1 = d3.scaleBand()
        .padding(0.1)

      this.y = d3.scaleLinear()
      this.z = d3.scaleOrdinal()
        
      this.xAxis = d3.axisBottom(this.x0)
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
      const data = transformMultiData(this.keys, this.multiData, this.year)

      // axis and domain setup
      this.x0.domain(data.map(r => r.stage))
      this.x1.domain(this.keys).rangeRound([0, this.x0.bandwidth()])
      this.y.domain([0, d3.max(data, r => r.highest )]).range([this.height, 0]).nice()

      this.z.domain(this.keys).range(this.colours)
      
      this.xAxisGroup
        .call(this.xAxis)
      this.yAxisGroup
        .call(this.yAxis)

      this.yAxisLabel
        .text(this.yAxisTitle)
      
      // Remove 
      this.g.select('.multi-bars').remove()

      const multiBarsGroup = this.g.append("g")
        .attr('class', 'multi-bars')
        .selectAll(".multi-bars")
        .data(data)
      
      const multiBars = multiBarsGroup.enter().append("g")
          .attr("transform", (d) => { 
            return "translate(" + this.x0(d.stage) + ",0)"; 
          })
        .selectAll("rect")
        .data((d) => { 
          return this.keys.map(function(key) { return {key: key, value: d[key]}; });
        })
      
      multiBars.enter().append("rect")
          .attr("x", (d) => { return this.x1(d.key); })
          .attr("y", (d) => { return this.y(d.value); })
          .attr("width", this.x1.bandwidth())
          .attr("height", (d) => { return this.height - this.y(d.value); })
          .attr("fill", (d) => { return this.z(d.key); })
          .attr('fillOpacity', 0)
        .on('mousedown', (d) => {
          this.$emit('click', d)
        })
        .on('mouseover', (d) => {
          this.$emit('mouseover', d)
        })
        .on('mouseout', (d) => {
          this.$emit('mouseout', d)
        })
        .merge(multiBars)
        .transition(this.t)
          .attr('fillOpacity', 1)

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
  top: 0;
  width: auto;
}

.legend-table.table {
  border: none;

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

