// #import "@preview/cuti:0.3.0": show-cn-fakebold

#let init(doc) = {
  // page
  set page(width: auto, height: auto, margin: 8pt, fill: luma(242))
  // font
  set text(font: ((name: "libertinus serif", covers: "latin-in-cjk"), "Noto Serif CJK SC"), lang: "zh")
  // cuti
  // show: show-cn-fakebold
  // code
  show raw : set text(font: ("Cascadia Mono", "Noto Sans Mono CJK SC"))
  // math
  show math.equation: set text(font: "Cambria Math")
  // enum
  // set enum(numbering: n => text(numbering("1.", n), font: "libertinus serif"))
  doc
}

#let render-typ(doc, init: init) = {
  show: init
  eval(doc, mode: "markup")
}
