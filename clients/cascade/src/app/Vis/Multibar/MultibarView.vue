<template>
  <div class="multi-bar-view">
    <div class="year-slider">
      <year-slider
        :years="yearOptions"
        @yearChanged="yearChanged"
      ></year-slider>
    </div>

    <div class="scenarios-vis">
      <div class="multi-bar-vis">
        <multibar
          :h="300"
          :yAxisTitle="'Number of people'"
          :multiData="cascadeData"
          :year="year"
        />
      </div>

    </div>
  </div>
</template>

<script>
import { transformCascadeData } from '../data-transform'
import Multibar from './Multibar.vue'
import YearSlider from '../YearSlider.vue'

export default {
  components: {
    Multibar,
    YearSlider,
  },
  props: {
    scenariosData: Object,
    colourScheme: Array
  },
  data() {
    return {
      result: null,
      resultsOptions: [],
      year: null,
      yearOptions: [],
      cascadeData: {},
      colorScheme: this.colourScheme || null
    }
  },
  watch: {
    scenariosData(newData) {
      if (newData) {
        this.updateCascadeData(newData)
      }
    },
    colourScheme(newData) {
      this.colours = newData
    }
  },
  methods: {
    updateCascadeData(d) {
      const transformed = transformCascadeData(d)

      this.resultsOptions = transformed.results
      this.result = transformed.results[0]

      this.yearOptions = transformed.years
      this.year = transformed.years[0]

      this.cascadeData = transformed
    },
    yearChanged(year) {
      this.year = year
    },
  }
}
</script>
<style lang="scss" scoped>
.scenarios-vis {
  .stacked-cascade-vis {
    display: flex;
    flex-wrap: wrap;

    .chart {
      width: 33%;
    }
  }
}

.year-slider {
  width: 100%;
  margin: 0 auto;
}

@media only screen and (min-width: 800px) {
  .year-slider {
    width: 80%;
  }
}

@media only screen and (min-width: 1200px) {
  .year-slider {
    width: 60%;
  }
}
</style>