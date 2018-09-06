import DropDown from './app/Dropdown.vue'
import help from './app/HelpLink.vue'

/**
 * You can register global components here and use them as a plugin in your main Vue instance
 */

const GlobalComponents = {
  install (Vue) {
    Vue.component('drop-down', DropDown)
    Vue.component('help', help)
  }
}

export default GlobalComponents
