<template>
  <div class="multi-bar-view">
    <div class="selections">      
      <label>
        Year
        <select class="select" v-model="year">
          <option v-for="option in yearOptions" :key="option" :value="option">
            {{ option }}
          </option>
        </select>
      </label>
    </div>

    <div class="scenarios-vis">
      <div class="multi-bar-vis">
        <h4>Scenarios</h4>
        <multibar
          :h="300"
          :yAxisTitle="'Number of people'"
          :multiData="cascadeData"
          :year="year"
          :colourScheme="colours"
        />
      </div>

      <div class="stacked-cascade-vis">
        <div class="chart" v-for="option in resultsOptions" :key="option">
          <h4>{{option}}</h4>
          <stacked-cascade
            :h="180"
            :yAxisTitle="'Number of people'"
            :cascadeData="cascadeData"
            :year="year"
            :scenario="option"
            :legendDisplay="true"
            :defaultTotal="true"
            :colourScheme="colours" />
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { transformCascadeData } from '../data-transform'
import Multibar from './Multibar.vue'
import StackedCascade from '../StackedCascade/StackedCascade.vue'

export default {
  components: {
    Multibar,
    StackedCascade,
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
      colours: this.colourScheme || null
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
    }
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

.scenarios-vis {
  display: flex;

  .multi-bar-vis {
    width: 50%;
  }
  .stacked-cascade-vis {
    width: 50%;
    
    .chart {
      margin-bottom: 1rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid #e4ecfc;
    }
  }

  h4 {
    font-size: 16px;
    font-weight: bold;
  }
}
</style>