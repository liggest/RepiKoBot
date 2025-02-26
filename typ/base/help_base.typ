#import "@preview/cuti:0.3.0": show-cn-fakebold

#let theme-color = rgb("#f8b63b")
#let bg-color = luma(242)
#let text-bg-color = luma(232)

#let init(doc) = {
  // page
  set page(width: auto, height: auto, margin: 8pt, fill: bg-color)
  // font
  set text(font: ((name: "Cascadia Code", covers: "latin-in-cjk"), "Noto Sans CJK SC"), lang: "zh")
  // cuti
  show: show-cn-fakebold
  // code
  show raw : set text(font: ("Cascadia Mono", "Noto Sans Mono CJK SC"))
  show raw.where(lang: "rpk") : set raw(syntaxes: "../asset/LSparser.sublime-syntax")
  show raw.where(lang: "rpko") : set raw(syntaxes: "../asset/LSparser-option.sublime-syntax")
  show raw.where(block: false): set raw(lang: "rpko", syntaxes: "../asset/LSparser-option.sublime-syntax")
  // show raw.where(lang: "rpk", block: true) : set text(size: 1.25em)
  show raw.where(lang: "rpko", block: true) : set text(size: 1.25em)
  show raw.where(block: false) : set text(size: 1.25em)
  // math
  // show math.equation: set text(font: "Cambria Math")
  // enum
  // set enum(numbering: n => text(numbering("1.", n), font: "libertinus serif"))
  doc
}

#let small-split-gen(inset: (left: 0.25em)) = {
  box(text("/", fill: luma(192), size: 0.8em), inset: inset)
}

#let small-split = small-split-gen()

#let render-names(names) = context {
  let name-content = heading(level: 2, names.join(small-split))
  // [ 
  //   #name-content
  //   #block(inset: (left: 0.5em, bottom: -0.5em, top: -0.25em))[
  //     #line(length: measure(name-content).width - 0.5em, stroke: gradient.linear(theme-color, theme-color, theme-color, luma(242)))
  //   ]
  // ]
  box(outset: (bottom: 0.5em, left: -0.5em), stroke: (bottom: gradient.linear(theme-color, theme-color, theme-color, bg-color)))[#name-content]
}

#let render-description(description) = {
  block(inset: (left: 2em), eval(description, mode: "markup"))
}

#let render-output(output, small: false) = {
  block(fill: text-bg-color, radius: 2pt, outset: 4pt, spacing: 4pt)[
    #h(0.75em)
    #box(inset: (right: 0em), width: 0.5em, text(emoji.triangle.r, size: if small { 1em } else { 1.25em }))
    #set text(size: 0.8em)
    #eval(output, mode: "markup")
  ]
}

#let render-hint(hint, small: false) = {
  block(fill: text-bg-color, radius: 2pt, outset: 4pt, spacing: 4pt)[
    #h(0.75em)
    #box(inset: (right: 0em), width: 0.5em, text(emoji.info, size: if small { 1em } else { 1.25em }))
    #set text(size: 0.8em) if small
    #eval(hint, mode: "markup")
  ]
}

#let render-plain(plain, small: false) = {
  block(fill: text-bg-color, radius: 2pt, outset: 4pt, spacing: 4pt)[
    #set text(size: 0.8em) if small
    #eval(plain, mode: "markup")
  ]
}

#let render-one-example(example) = {
  if "input" in example {
    block(fill: text-bg-color, radius: 2pt, outset: 4pt, spacing: 4pt, raw(example.input, lang: "rpk", block: true))
  }
  if "output" in example {
    v(2pt)
    render-output(example.output, small: true)
  }
  if "hint" in example {
    v(2pt)
    render-hint(example.hint, small: true)
  }
  if "plain" in example {
    v(2pt)
    render-plain(example.plain, small: true)
  }
  v(1em)
}

#let render-examples(examples) = {
  examples.map(render-one-example).join()
}

#let render-misc(misc) = {
  set text(size: 0.8em)
  block(fill: text-bg-color, radius: 2pt, outset: 4pt)[
    #eval(misc.trim(), mode: "markup")
  ]
}

// #let small-split-option = {
//   box(text("/", fill: luma(192), size: 0.8em), inset: (left: 0.25em, right: 0.25em, bottom: 0.05em))
// }

#let small-split-option = small-split-gen(inset: (left: 0.25em, right: 0.25em, bottom: 0.05em))

#let render-option-names(names, params: none) = {
  if params != none {
    names.push(names.pop() + " " + params)
  }
  names.map(raw.with(lang: "rpko")).join(small-split-option)
}

#let render-one-option(option) = {
  block(fill: text-bg-color, radius: 2pt, outset: 4pt, spacing: 4pt, {
    if "names" in option {
      render-option-names(option.names, params: option.at("params", default: none))
    }
    h(2em)
    if "description" in option {
      eval(option.description, mode: "markup")
    }
  })
  if "hint" in option {
    v(2pt)
    render-hint(option.hint)
  }
  v(8pt)
}

#let render-options(options) = {
  set text(size: 0.8em)
  // show raw: set text(size: 1.25em)
  options.map(render-one-option).join()
  v(-4pt)
}

#let render-help(help_dict) = {

  // repr(help_dict)

  // pagebreak()

  for (key, value) in help_dict {
    if key.starts-with("_") {
      continue
    }
    if key.starts-with("names") {
      render-names(value)
    }
    else if key.starts-with("description") and value != "" {
      render-description(value)
    }
    else if key.starts-with("examples") {
      place(dx: -0.5em, dy: -0.5em)[
        #rect(stroke: theme-color, outset: -0.15em, radius: 2pt)[例]
      ]
      block(inset: (left: 2em), render-examples(value))
      v(-0.75em)
    }
    else if key.starts-with("misc") {
      place(dx: -0.15em, dy: -0.15em, emoji.label)
      block(inset: (left: 2em), render-misc(value))
    }
    else if key.starts-with("options") {
      place(dx: -0.5em, dy: -0.5em)[
        #rect(stroke: theme-color, outset: -0.15em, radius: 2pt)[选项详细]
      ]
      v(1.5em)
      v(4pt)
      block(inset: (left: 2em), render-options(value))
    }
  }

  // if "names" in help_dict {
  //   render-names(help_dict.names)
  // }

  // if "description" in help_dict and help_dict.description != "" {
  //   block(inset: (left: 2em), help_dict.description)
  // }

  // let order = help_dict.at("order", default: ("examples", "misc", "options"))
  // let renders = (
  //   examples: () => {
  //     if "examples" in help_dict {
  //       place(dx: -0.5em, dy: -0.5em)[
  //         #rect(stroke: theme-color, outset: -0.15em, radius: 2pt)[例]
  //       ]
  //       block(inset: (left: 2em), render-examples(help_dict.examples))
  //       v(-0.75em)
  //     }
  //   },
  //   misc: () => {
  //     if "misc" in help_dict {
  //       place(dx: -0.15em, dy: -0.15em, emoji.label)
  //       block(inset: (left: 2em), render-misc(help_dict.misc))
  //     }
  //   },
  //   options: () => {
  //     if "options" in help_dict {
  //       place(dx: -0.5em, dy: -0.5em)[
  //         #rect(stroke: theme-color, outset: -0.15em, radius: 2pt)[选项详细]
  //       ]
  //       v(1.5em)
  //       v(4pt)
  //       block(inset: (left: 2em), render-options(help_dict.options))
  //     }
  //   }
  // )

  // for item in order {
  //   if item in renders {
  //     renders.at(item)()
  //   }
  // }
}

#let small-split-cmd-list = small-split-gen(inset: (left: 0.25em, bottom: 0.05em))

#let render-list-names(names) = {
  names.map(raw.with(lang: "rpk")).join(small-split-cmd-list)
}

#let render-list-item(item) = [
  #render-list-names(item.names)
  #h(0.5em)
  #eval(item.description, mode: "markup")
]

#let render-cmd-list(items) = {
  items.sorted(key: it => it.names).map(render-list-item).join(parbreak())
}
