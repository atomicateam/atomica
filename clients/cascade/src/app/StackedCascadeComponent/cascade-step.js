/* eslint-disable */

function CascadeStep(context) {
  this._context = context;
  this._t = 1;
}

CascadeStep.prototype = {
  areaStart: function() {
    this._line = 0;
  },
  areaEnd: function() {
    this._line = NaN;
  },
  lineStart: function() {
    this._x = this._y = NaN;
    this._point = 0;
  },
  lineEnd: function() {
    if (0 < this._t && this._t < 1 && this._point === 2) {
      this._context.lineTo(this._x, this._y);
    }
    if (this._line || (this._line !== 0 && this._point === 1)) {
      this._context.closePath();
    }
    if (this._line >= 0) {
      this._t = 1 - this._t, this._line = 1 - this._line;
    }
  },
  point: function(x, y) {
    x = +x, y = +y;
    switch (this._point) {
      case 0: 
        this._point = 1;
        this._line ? 
          this._context.lineTo(x, y) :
          this._context.moveTo(x, y);
        break;
      case 1: this._point = 2; // proceed
      default: {
        if (this._t <= 0) {
          var x1 = this._x * (1 - this._t) + x * this._t;
          var x2 = (this._x + x) / 2;
          this._context.lineTo(this._x, this._y);
          this._context.lineTo(x2, y);
        } else {
          var x1 = this._x * (1 - this._t) + x * this._t;
          var x2 = (this._x + x) / 2;
          this._context.lineTo(x2, this._y);
          this._context.lineTo(x1, y);
        }
      }
    }
    this._x = x, this._y = y;
  }
};

export default function(context) {
  return new CascadeStep(context);
}
