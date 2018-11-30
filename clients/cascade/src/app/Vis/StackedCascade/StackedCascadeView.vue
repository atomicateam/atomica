<template>
  <div class="stacked-cascade-view">
    <div class="selections" v-if="resultsOptions.length > 1">
      <label>
        <select class="select" v-model="result">
          <option v-for="option in resultsOptions" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
      </label>
    </div>

    <div class="chart-options">
      <div class="year-slider">
        <year-slider
          :years="yearOptions"
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

    <div class="chart">
      <stacked-cascade class="cascade"
        :h="300"
        :yAxisTitle="'Number of people'"
        :cascadeData="updatedData"
        :year="year"
        :scenario="result"
        :colourScheme="colours"
        :legendDisplay="true" 
        @chartUpdated="chartUpdated" />
    </div>
  </div>
</template>

<script>
import { transformCascadeData } from '../data-transform'
import StackedCascade from './StackedCascade.vue'
import YearSlider from '../YearSlider.vue'
import ExportGraph from '../ExportGraph.vue'

export default {
  components: {
    StackedCascade,
    YearSlider,
    ExportGraph,
  },
  props: {
    cascadeData: Object,
    colourScheme: Array
  },
  data() {
    return {
      result: null,
      resultsOptions: [],
      year: null,
      yearOptions: [],
      updatedData: {},
      colours: this.colourScheme || null,
      chartSvg: null,
      chartWidth: 300,
      chartHeight: 400,
    }
  },
  computed: {
    filename() {
      return `cascade_plot_${this.year}`
    },
  },
  watch: {
    cascadeData(newData) {
      if (newData) {
        this.updateCascadeData(newData)
      }
    },
    colourScheme(newData) {
      this.colours = newData
    }
  },
  mounted() {
  },
  methods: {
    updateCascadeData(d) {
      const transformed = transformCascadeData(d)

      this.resultsOptions = transformed.results
      this.result = transformed.results[0]

      this.yearOptions = transformed.years
      this.year = transformed.years[0]

      this.updatedData = transformed
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
.selections {
  border-bottom: 1px solid #e4ecfc;
  padding: 1rem;
  margin-bottom: 1rem;

  .select {
    margin-right: 1rem;
  }
}

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

.chart {
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
  margin: 0 auto;
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