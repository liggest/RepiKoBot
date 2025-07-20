#import "@preview/mitex:0.2.5": mitex

#let init(doc) = {
  // page
  set page(width: auto, height: auto, margin: 4pt, fill: luma(242))
  // font
  set text(font: ((name: "libertinus serif", covers: "latin-in-cjk"), "Noto Sans CJK SC"), lang: "zh")
  // math
  // show math.equation: set text(font: "Cambria Math")
  // show math.equation: it => {
  //   set text(font: "Cambria Math")
  //   show regex("\p{script=Han}"): set text(font: "Noto Sans CJK SC")
  //   it
  // }
  doc
}

#let render-tex(tex, init: init) = {
  show: init
  mitex(tex)
}
