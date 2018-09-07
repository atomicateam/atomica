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
    <!--<dialog-drag id="dialog-1">-->
      <!--<p> Test dialog</p>-->
    <!--</dialog-drag>-->
    <!--<drop-area @drop='drop' @click='console.log("faosdifu")' style="width:100px">-->
      <!--<p>Drop Here</p>-->
    <!--</drop-area>-->


    <button @click="newDialog('mishy')">hiii</button>
    <br><br><br><br><br><br><br><br><br><br>
    <br><br><br><br><br><br><br><br><br><br>
    <button @click="newDialog('mashy')">fai</button>


    <div class="dialogs">
      <div v-for="val in vals">
        <dialog-drag v-if='doshow[val]'
                     :class='dialog-2'
                     :key='val'
                     :id='val'
                     :ref='val'
                     @close='removeDialog(val)'
                     @drag-end='dialogDragEnd'
                     @drag-start='selectDialog'
                     @move='dialogDragEnd'>

          <span slot='title'> {{ dialog.name }} </span>
          <p>{{dialog.content}}</p>
        </dialog-drag>
      </div>
    </div>
  </div>
</template>

<script>

  export default {
    name: 'example',

    data () {
      return {
        vals: [0,1,2,3],
        doshow: [true,true,true,true],
        styles: [
          { name: 'dialog-1', options: { width: 400 } },
          { name: 'dialog-2', options: { width: 150, buttonPin: false } },
          { name: 'dialog-3' }
        ],
        style: null,
        selected: null,
        dialogWidth: 400,
        droppeds: [],
        x:-1,
        y:-1,
        dialogs: [],
      }
    },

    created () {
      this.addListener()

      for (let i=0; i<4; i++) {
        this.newDialog(i)
      }
    },

    methods: {

      addListener() {
        document.addEventListener('mousemove', this.onMouseUpdate, false);
      },

      onMouseUpdate(e) {
        this.x = e.pageX;
        this.y = e.pageY;
//        console.log(this.x, this.y);
      },

      drop (index) {
        console.log('ok?')
        console.log(index)
//        let index = this.findDialog(id)
        if (index !== null) {
          console.log('a?')
          this.droppeds.push(this.dialogs[index])
          console.log('b?')
          this.dialogs.splice(index, 1)
          console.log('c?')
        }
      },
      unDrop (id) {
        let index = this.findDialog(id, this.droppeds)
        if (index !== null) {
          this.dialogs.push(this.droppeds[index])
          this.droppeds.splice(index, 1)
        }
      },
      newDialog (sId) {
        if (sId === null) sId = Math.floor(Math.random() * this.styles.length)
        return this.dialogs.push(this.dialog(this.styles[0], sId))
      },
      removeDialog (val) {
        console.log('rem!')
        console.log(val)
        this.doshow[val] = false
        console.log(this.doshow)
        let id = val
        console.log('ah!')
        console.log(val)
        let index = this.findDialog(id)
        console.log('beh!')
        console.log(index)
        this.dialogs.splice(index, 1)
        if (this.selected && this.selected.id === id) this.selected = null
      },
      findDialog (id, dialogs) {
        console.log('heyeye')
        console.log(this.dialogs)
        if (!dialogs) dialogs = this.dialogs
        let index = dialogs.findIndex((val) => {
          return val.id === id
        })
        return (index > -1) ? index : null
      },
      dialog (style, myid) {
        let id = myid // String(this.dialogId)
//        this.dialogId++
        let name = 'Dialog ' + id
        let content = 'foo' //rndText()
        let options = {}
        if (style.options) options = Object.assign({}, style.options)
        if (!options.left) options.left = this.x
        if (!options.top) options.top = this.y
        return { id, name, content, style, options }
      },
      dialogDragEnd (obj) {
        let index = this.findDialog(obj.id)
//        this.$set(this.dialogs[index].options, 'left', obj.left)
//        this.$set(this.dialogs[index].options, 'top', obj.top)
      },
      selectDialog (obj) {
        let index = this.findDialog(obj.id)
        this.selected = this.dialogs[index]
      }
    }
  }
</script>

<!--<style src="../vue-dialog-drag/dist/vue-dialog-drag.css"></style>-->
<!--<style src="../vue-dialog-drag/dist/drop-area.css"></style>-->

<!-- optional dialog styles, see example -->
<!--<style src="vue-dialog-drag/dist/dialog-styles.css"></style>-->

<style>
  .dialog-drag{-webkit-animation-duration:.2s;-webkit-animation-name:dialog-anim;-webkit-animation-timing-function:ease-in;-webkit-box-shadow:1px 1px 1px rgba(0,0,0,.5);animation-duration:.2s;animation-name:dialog-anim;animation-timing-function:ease-in;background-color:#fff;border:2px solid #1aad8d;box-shadow:1px 1px 1px rgba(0,0,0,.5);height:auto;position:absolute;width:auto;z-index:101}.dialog-drag .dialog-header{background-color:#1aad8d;color:#fff;font-size:.9em;padding:.25em 3em .25em 1em;position:relative;text-align:left;width:auto}.dialog-drag .dialog-header .buttons{margin:.25em .25em 0 0;position:absolute;right:0;top:0;z-index:105}.dialog-drag .dialog-header button.close,.dialog-drag .dialog-header button.pin{-webkit-box-shadow:none;background:transparent;border:none;box-shadow:none;color:#fff}.dialog-drag .dialog-header button.close:hover,.dialog-drag .dialog-header button.pin:hover{color:#e3a826}.dialog-drag .dialog-header button.close:after{content:"\2716"}.dialog-drag .dialog-header button.pin:after{content:"\1F513"}.dialog-drag .dialog-body{padding:1em}.dialog-drag.fixed{-moz-user-select:auto;-ms-user-select:auto;-webkit-user-select:auto;border-color:#e3a826;user-select:auto}.dialog-drag.fixed button.pin{font-weight:700}.dialog-drag.fixed button.pin:after{content:"\1F512"}@-webkit-keyframes dialog-anim{0%{-webkit-transform:scaleX(.1);opacity:0;transform:scaleX(.1)}50%{-webkit-transform:rotate(1deg);transform:rotate(1deg)}to{opacity:1}}@keyframes dialog-anim{0%{-webkit-transform:scaleX(.1);opacity:0;transform:scaleX(.1)}50%{-webkit-transform:rotate(1deg);transform:rotate(1deg)}to{opacity:1}}
  .drop-area,.over{-ms-flex-align:center;-ms-flex-pack:center;-ms-flex-wrap:wrap;-webkit-box-align:center;-webkit-box-pack:center;align-items:center;display:-webkit-box;display:-ms-flexbox;display:flex;flex-wrap:wrap;justify-content:center}.drop-area{border:2px dotted #6c938a;margin-bottom:.5em;min-height:10em;position:relative;text-align:center}.drop-area small{color:#6c938a}.over{background-color:rgba(227,168,38,.5);height:100%;left:0;pointer-events:none;position:absolute;top:0;width:100%;z-index:105}.dropped{background-color:#fff;border:1px dashed #1aad8d;cursor:pointer;margin:.125em}.dropped:hover{border-color:#e3a826}.dropped:hover .icon svg{fill:#e3a826}.dropped .name{font-size:.6em;margin:0 .5em .25em}.dropped .icon,.dropped .icon svg{margin:0;padding:0}.dropped .icon svg{background:transparent;fill:#1aad8d}
  .dialog-drag{min-width:10em;background-color:#e6eee9;box-shadow:2px 2px 1px rgba(0,0,0,0.5)}.dialog-1.dialog-drag{border:#1aad8d dashed 2px;background-color:#fff;box-shadow:1px 1px 1px rgba(0,0,0,0.5);}.dialog-1.dialog-drag .dialog-header{background-color:transparent;}.dialog-1.dialog-drag .dialog-header .buttons button{color:#1aad8d}.dialog-1.dialog-drag .dialog-header .title{display:none}.dialog-drag.dialog-1.fixed{border:#1aad8d solid 2px}.dialog-2.dialog-drag{border-color:#1aad8d;}.dialog-2.dialog-drag .dialog-header{background-color:#1aad8d;color:#fff;}.dialog-2.dialog-drag .dialog-header .buttons button{color:#fff}.dialog-3.dialog-drag{border:none;background-color:#fdfaf1;animation-name:dialog-3-anim;}.dialog-3.dialog-drag .dialog-header{background-color:#e3a826;color:#fff;}.dialog-3.dialog-drag .dialog-header .buttons button{color:#f9edd2;text-shadow:none;}.dialog-3.dialog-drag .dialog-header .buttons button:hover{color:#fff;text-shadow:1px 1px 1px rgba(0,0,0,0.5)}.dialog-drag.dialog-3.fixed{margin:2em;outline:#1aad8d 2px dashed;outline-offset:.25em}@-moz-keyframes dialog-3-anim{0%{opacity:0;transform:scaleX(.1) scaleX(3)}100%{opacity:1}}@-webkit-keyframes dialog-3-anim{0%{opacity:0;transform:scaleX(.1) scaleX(3)}100%{opacity:1}}@-o-keyframes dialog-3-anim{0%{opacity:0;transform:scaleX(.1) scaleX(3)}100%{opacity:1}}@keyframes dialog-3-anim{0%{opacity:0;transform:scaleX(.1) scaleX(3)}100%{opacity:1}}
</style>