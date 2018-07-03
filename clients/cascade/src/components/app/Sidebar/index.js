import Sidebar from './SideBar.vue'

const SidebarStore = {
  showSidebar: false,
  sidebarLinks: [
    {
      name: 'Frameworks',
      icon: 'ti-ruler-pencil',
      path: '/frameworks'
    },
    {
      name: 'Projects',
      icon: 'ti-view-grid',
      path: '/projects'
    },
    {
      name: 'Baseline',
      icon: 'ti-pulse',
      path: '/baseline'
    },
    {
      name: 'Analysis',
      icon: 'ti-control-shuffle',
      path: '/analysis'
    },
    {
      name: 'Help',
      icon: 'ti-help',
      path: '/help'
    },
    {
      name: 'Contact',
      icon: 'ti-comment-alt',
      path: '/contact'
    },
    {
      name: 'About',
      icon: 'ti-shine',
      path: '/about'
    },
  ],

  displaySidebar (value) {
    this.showSidebar = value
  },
}

const SidebarPlugin = {

  install (Vue) {
    Vue.mixin({
      data () {
        return {
          sidebarStore: SidebarStore
        }
      }
    })

    Object.defineProperty(Vue.prototype, '$sidebar', {
      get () {
        return this.$root.sidebarStore
      }
    })
    Vue.component('side-bar', Sidebar)
  }
}

export default SidebarPlugin
