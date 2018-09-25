import DropDown from './app/Dropdown.vue'
import help from './app/HelpLink.vue'
import DialogDrag from 'vue-dialog-drag'

/**
 * You can register global components here and use them as a plugin in your main Vue instance
 */

const GlobalComponents = {
  install (Vue) {
    Vue.component('drop-down', DropDown)
    Vue.component('help', help)
    Vue.component('DialogDrag', DialogDrag)
  }
}

export default GlobalComponents
