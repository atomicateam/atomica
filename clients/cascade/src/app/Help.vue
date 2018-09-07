<!--
Help page -- ideally will have mostly in-app help a la HIV

Last update: 2018-08-18
-->

<!--<template>-->
<!--<div class="SitePage">-->
<!--<p>We are in the process of writing a user guide.</p>-->
<!--<p>For assistance in the meantime, please email <a href="mailto:info@cascade.tools">info@cascade.tools</a>.</p>-->
<!--</div>-->
<!--</template>-->


<!--&lt;!&ndash; Add "scoped" attribute to limit CSS to this component only &ndash;&gt;-->
<!--<style scoped>-->
<!--</style>-->





<template>
  <div id="app">

    <button @click="createDialogs()">CREATE</button>
    <br><br><br><br><br><br><br><br><br><br>


    <div v-for="val in vals">
      <button @click="maximize(val)" data-tooltip="Show legend"><i class="ti-menu-alt"></i></button>
      <br><br><br>
    </div>

    <div class="dialogs">
      <dialog-drag v-for="dialog,key in openDialogs"
                   :id="dialog.id"
                   :key="key"
                   @close="minimize(dialog.id)"
                   :options="dialog.options">

        <span slot='title'> {{ dialog.name }} </span>
        <p>{{dialog.content}}</p>
      </dialog-drag>
    </div>
  </div>
</template>

<script>

  export default {
    name: 'example',

    data () {
      return {
        vals: [0,1,2,3],
        closedDialogs: [],
        openDialogs: [],
        mousex:-1,
        mousey:-1,
      }
    },

    created () {
      this.addListener()
    },

    methods: {

      addListener() {
        document.addEventListener('mousemove', this.onMouseUpdate, false);
      },

      onMouseUpdate(e) {
        this.mousex = e.pageX;
        this.mousey = e.pageY;
      },

      createDialogs() {
        for (let val in this.vals) {
          this.newDialog(val, 'Dialog '+val, 'This is test '+val)
        }
      },

      // Create a new dialog
      newDialog (id, name, content) {
        let options = {}
        let properties = { id, name, content, options }
        return this.closedDialogs.push(properties)
      },

      findDialog (id, dialogs) {
        if (!dialogs) dialogs = this.openDialogs
        let index = dialogs.findIndex((val) => {
          return String(val.id) === String(id) // Force type conversion
        })
        return (index > -1) ? index : null
      },

      // "Show" the dialog
      maximize(id) {
        let index = this.findDialog(id, this.closedDialogs)
        if (index !== null) {
          this.closedDialogs[index].options.left = this.mousex // Before opening, move it to where the mouse currently is
          this.closedDialogs[index].options.top = this.mousey
          this.openDialogs.push(this.closedDialogs[index])
          this.closedDialogs.splice(index, 1)
        }
      },

      // "Hide" the dialog
      minimize(id) {
        let index = this.findDialog(id)
        if (index !== null) {
          this.closedDialogs.push(this.openDialogs[index])
          this.openDialogs.splice(index, 1)
        }
      },

    }
  }
</script>

<style>

</style>