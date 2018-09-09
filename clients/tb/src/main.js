// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'

// Plugins
import Simplert from 'vue2-simplert-plugin' // Simple alert plugin
require('vue2-simplert-plugin/dist/vue2-simplert-plugin.css')
import VModal from 'vue-js-modal' // Modal dialogs plugin
import VueProgressBar from 'vue-progressbar' // Progress bar plugin
import PopupSpinner from './app/PopupSpinner' // PopupSpinner plugin
import SideBar from './app/Sidebar' // SideBar plugin
import Notifications from './app/NotificationPlugin'
import DialogDrag from 'vue-dialog-drag'

import GlobalComponents from './globalComponents'
import GlobalDirectives from './globalDirectives'
import App from './App'
import router from './router'
import store from './store'

Vue.config.productionTip = false
// library imports
import Chartist from 'chartist'
import 'bootstrap/dist/css/bootstrap.css'
import './sass/project.scss'
import 'es6-promise/auto'

// plugin setup
Vue.use(GlobalComponents);
Vue.use(GlobalDirectives);
Vue.use(Notifications);
Vue.use(SideBar);
Vue.use(Simplert);
Vue.use(VModal);
Vue.use(VueProgressBar, {
  color: 'rgb(0, 0, 255)',
  failedColor: 'red',
  thickness: '3px',
  transition: {
    speed: '0.2s',
    opacity: '0.6s',
    termination: 300
  }       
});
Vue.use(PopupSpinner);
Vue.use(DialogDrag);

// global library setup
Object.defineProperty(Vue.prototype, '$Chartist', {
  get () {
    return this.$root.Chartist
  }
})

// CK: if we decide we want to do global imputs in future, so we can use e.g. this.$utils.sleep() in the components instead of import utils and then utils.sleep()
// import utils from '@/services/utils'
// Vue.prototype.$utils = utils

Vue.prototype.$globaltool = 'tb' // CASCADE-TB DIFFERENCE, duh :)

new Vue({
  el: '#app',
  render: h => h(App),
  router,
  store,
  template: '<App/>',
  components: { App },
  data: {
    Chartist: Chartist
  }
})
