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
      <dialog-drag v-for='dialog,key in openDialogs'
        :class='dialog.style.name'
        :key='dialog.id'
        :id='dialog.id'
        :ref='"dialog-" + dialog.id'
        @close='minimize(dialog.id)'
        :options='dialog.options'>

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
        let style = { name: 'dialog-2', options: { width: 150, buttonPin: false } }
        let options = {}
        options.left = this.mousex
        options.top = this.mousey
        let properties = { id, name, content, style, options }
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
          this.closedDialogs[index].options.left = this.x
          this.closedDialogs[index].options.top = this.y
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
  .dialog-drag{-webkit-animation-duration:.2s;
    -webkit-animation-name:dialog-anim;
    -webkit-animation-timing-function:ease-in;
    -webkit-box-shadow:1px 1px 1px rgba(0,0,0,.5);
    animation-duration:.2s;
    animation-name:dialog-anim;
    animation-timing-function:ease-in;
    background-color:#fff;
    border:2px solid #1aad8d;
    box-shadow:1px 1px 1px rgba(0,0,0,.5);
    height:auto;
    position:absolute;
    width:auto;
    z-index:101}

  .dialog-drag .dialog-header{background-color:#1aad8d;
    color:#fff;
    font-size:.9em;
    padding:.25em 3em .25em 1em;
    position:relative;
    text-align:left;
    width:auto}

  .dialog-drag .dialog-header .buttons{margin:.25em .25em 0 0;
    position:absolute;
    right:0;
    top:0;
    z-index:105}

  .dialog-drag .dialog-header button.close,.dialog-drag .dialog-header button.pin{-webkit-box-shadow:none;
    background:transparent;
    border:none;
    box-shadow:none;
    color:#fff}
  .dialog-drag .dialog-header button.close:hover,.dialog-drag .dialog-header button.pin:hover{color:#e3a826}
  .dialog-drag .dialog-header button.close:after{content:"\2716"}
  .dialog-drag .dialog-header button.pin:after{content:"\1F513"}
  .dialog-drag .dialog-body{padding:1em}

  .dialog-drag.fixed{-moz-user-select:auto;
    -ms-user-select:auto;
    -webkit-user-select:auto;
    border-color:#e3a826;
    user-select:auto}
  .dialog-drag.fixed button.pin{font-weight:700}
  .dialog-drag.fixed button.pin:after{content:"\1F512"}

  @-webkit-keyframes dialog-anim{0%{-webkit-transform:scaleX(.1);
    opacity:0;
    transform:scaleX(.1)}
    50%{-webkit-transform:rotate(1deg);
      transform:rotate(1deg)}
    to{opacity:1}
  }

  @keyframes dialog-anim{0%{-webkit-transform:scaleX(.1);
    opacity:0;
    transform:scaleX(.1)}
    50%{-webkit-transform:rotate(1deg);
      transform:rotate(1deg)}
    to{opacity:1}
  }

  .dialog-drag{min-width:10em;
    background-color:#e6eee9;
    box-shadow:2px 2px 1px rgba(0,0,0,0.5)}

  .dialog-1.dialog-drag{border:#1aad8d dashed 2px;
    background-color:#fff;
    box-shadow:1px 1px 1px rgba(0,0,0,0.5);
  }
  .dialog-1.dialog-drag .dialog-header{background-color:transparent;
  }
  .dialog-1.dialog-drag .dialog-header .buttons button{color:#1aad8d}
  .dialog-1.dialog-drag .dialog-header .title{display:none}
  .dialog-drag.dialog-1.fixed{border:#1aad8d solid 2px}

  .dialog-2.dialog-drag{border-color:#1aad8d;}
  .dialog-2.dialog-drag .dialog-header{background-color:#1aad8d; color:#fff; }
  .dialog-2.dialog-drag .dialog-header .buttons button{color:#fff}

  .dialog-3.dialog-drag{border:none; background-color:#fdfaf1; animation-name:dialog-3-anim;}
  .dialog-3.dialog-drag .dialog-header{background-color:#e3a826;color:#fff;}
  .dialog-3.dialog-drag .dialog-header .buttons button{color:#f9edd2;text-shadow:none;}
  .dialog-3.dialog-drag .dialog-header .buttons button:hover{color:#fff;text-shadow:1px 1px 1px rgba(0,0,0,0.5)}
  .dialog-drag.dialog-3.fixed{margin:2em;outline:#1aad8d 2px dashed; outline-offset:.25em}

  @-moz-keyframes dialog-3-anim{0%{opacity:0;
    transform:scaleX(.1) scaleX(3)}
    100%{opacity:1}
  }

  @-webkit-keyframes dialog-3-anim{0%{opacity:0;
    transform:scaleX(.1) scaleX(3)}
    100%{opacity:1}
  }

  @-o-keyframes dialog-3-anim{0%{opacity:0;
    transform:scaleX(.1) scaleX(3)}
    100%{opacity:1}
  }

  @keyframes dialog-3-anim{0%{opacity:0;
    transform:scaleX(.1) scaleX(3)}
    100%{opacity:1}
  }


</style>