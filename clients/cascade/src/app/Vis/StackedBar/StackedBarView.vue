<template>
  <div class="budget-view">

    <div class="chart-options">
      <div class="year-slider">
        <year-slider
          :years="yearOptions"
          :selected="yearOptions.length - 1"
          @yearChanged="yearChanged"
        ></year-slider>
      </div>

      <export-graph
        :filename="filename"
        :chartSvg="chartSvg"
        :chartWidth="chartWidth"
        :chartHeight="chartHeight"
      />
    </div>
    
    <div class="budget-vis">
      <div class="stacked-bar-vis">
        <stacked-bar
          :h="300"
          :yAxisTitle="'$/Year'"
          :stackedBarData="stackedBarData"
          :year="year"
          :legendDisplay="true"
          :colourScheme="colours"
          @chartUpdated="chartUpdated"
        />
      </div>

    </div>
  </div>
</template>

<script>
import { transformBudgetData } from '../data-transform'
import StackedBar from './StackedBar.vue'
import YearSlider from '../YearSlider.vue'
import ExportGraph from '../ExportGraph.vue'

export default {
  components: {
    StackedBar,
    YearSlider,
    ExportGraph,
  },
  props: {
    budgetData: Object,
    colourScheme: Array
 },
  data() {
    return {
      year: null,
      yearOptions: [],
      stackedBarData: {},
      colours: this.colourScheme || null,
      chartSvg: null,
      chartWidth: 300,
      chartHeight: 400,
    }
  },
  computed: {
    filename() {
      return `stackedbar_plot_${this.year}`
    },
  },
  watch: {
    budgetData(newData) {
      if (newData) {
        this.updateStackedBarData(newData)
      }
    },
    colourScheme(newData) {
      this.colours = newData
    }
  },
  methods: {
    updateStackedBarData(d) {
      const transformed = transformBudgetData(d)

      this.yearOptions = transformed.years
      this.year = transformed.years[0]

      this.stackedBarData = transformed
    },
    yearChanged(year) {
      this.year = year
    },

    chartUpdated(chartSvg, width, height) {
      this.chartSvg = chartSvg
      this.chartWidth = width
      this.chartHeight = height
    },
  }
}
</script>
<style lang="scss" scoped>

.chart-options {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}

.save-options {
  vertical-align: bottom;
  text-align: right;
  width: 100%;
  padding-bottom: 5px;
}

.budget-vis {
  max-width: 1200px;
  margin: 0 auto 20px;
  padding: 20px;
  border: 1px solid #dedede;
  background: #fff;
  border-radius: 3px;
  box-shadow: 0 2px 3px rgba(0,0,0,.05);
}

.year-slider {
  width: 100%;
}

@media only screen and (min-width: 800px) {
  .chart-options {
    display: flex;
    width: 90%;
  }
  .save-options {
    width: 20%;
    padding-top: 30px;
  }
  .year-slider {
    width: 80%;
  }
}
</style>