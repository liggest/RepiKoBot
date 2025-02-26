#import "../typ/base/help_base.typ": init, render-cmd-list

#show: init

// #let data = (
//   (names: (".AA", ".aa"), description: "基于AAMZ随机抽取AA"),
//   (names: (".hitokoto", ".htkt", ".一言"), description: "基于一言的短句分享"),
// )

#let data-override = (
  "aword": (names: (".hitokoto", ".htkt", ".一言")),
  "choose": (names: (".choose", ".选")),
  "duel": (names: (".duel", ".决斗", ".打牌", ".牌")),
  // "help": (names: (".help",)),
  "mahjong": (names: (".mahjong", ".麻将")),
  "tex": (names: (".tex",)),
  "voicevox": (names: (".voicevox", ".vv")),
  "ygocard": (names: (".ygocard", ".yc")),
  "ygocdb": (names: (".ygocdb", ".ycdb")),
)

#let data = {
  let cmds = (
    "AA", 
    "aword", 
    "calculate", 
    "choose", 
    "duel", 
    "help", 
    "luck", 
    "mahjong", 
    "roll", 
    "tex", 
    "translate", 
    "typst",
    "voicevox", 
    "ygocard", 
    "ygocdb", 
    "ygodraw"
  )
  
  array(
    cmds.map(
      cmd => {
        let item = data-override.at(cmd, default: (:))
        if "names" not in item or "description" not in item {
          let spec = toml("./" + cmd + "/general.toml")
          item.names = item.at("names", default: spec.names)
          item.description = item.at("description", default: spec.description.split().first())
        }
        item
      }
    )
  )
}

#render-cmd-list(data)

#render-cmd-list((
  (names: ("-hello",), description: "喵哈喽\~"),
))

查看指令详情，请使用 ```rpk .help 某指令名```
