# 地图预研迁移说明

本文件恢复自 Git 历史提交 `196dd7b` 中的 `docs/airport_operations/City_Airport_Market_List_v0.1.md`。
它是机场市场预研名单，不是当前正式项目配置；正式机场配置仍以 `config/city_airport_markets/` 为准。
原文内容保留如下。

---
# City Airport Market List v0.1

这个文件用于列城市/都市圈机场系统。当前先作为机场经营层的名单占位，避免机场名单散落在宏观或区域航空文档中。

## 建议字段

```text
city_airport_market_id
city_airport_market_name
region_id
market_type
base_passenger_scale
base_capacity_scale
primary_passenger_mix
transfer_hub_weight
slot_constraint_base
terminal_constraint_base
planned_capacity_projects
```

## 候选样板

```text
beijing_tianjin_airport_system
shanghai_yangtze_delta_gateway
pearl_river_delta_airport_system
chengdu_chongqing_airport_system
new_york_metro_airport_system
london_airport_system
paris_airport_system
dubai_doha_gulf_hub
singapore_bangkok_gateway
tokyo_seoul_gateway
delhi_mumbai_india_gateway
istanbul_eurasia_gateway
```

## 中国大陆城市机场市场

中国大陆城市机场市场先按城市/都市圈列，不拆成单机场经营对象。后续新增城市直接加入本表。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `beijing_airport_system` | 北京 | 首都 + 大兴，已是双机场 | 后续重点是双机场分工、时刻和国际/国内结构 |
| `shanghai_airport_system` | 上海 | 浦东 + 虹桥，已是双机场 | 预留南通新机场（南通市通州区二甲镇）；v2 作为长三角核心门户 seed 势能样板 |
| `guangzhou_airport_system` | 广州 | 白云单核心 | 预留佛山高明机场（广州新机场/珠三角枢纽）；v2 作为华南传统核心门户 seed 势能样板 |
| `shenzhen_airport_system` | 深圳 | 宝安单核心 | 预留惠州平潭机场承担深圳第二机场功能；v3 作为大湾区高商务增长门户 seed 势能样板 |
| `chengdu_airport_system` | 成都 | 双流 + 天府，已是双机场 | 适合测试新机场投放后的容量爬坡；v2 作为成渝双城门户 seed 势能样板 |
| `chongqing_airport_system` | 重庆 | 江北单核心 | 预留重庆璧山机场（璧山正兴场址）；v2 作为成渝双城门户 seed 势能样板 |
| `hangzhou_airport_system` | 杭州 | 萧山单核心 | 预留杭州第二机场（湖州德清方向传言/候选）；v2 作为长三角次级门户 seed 势能样板 |
| `nanjing_airport_system` | 南京 | 禄口单核心 | 第一版按禄口单机场经营，以禄口扩建和槽位升级为主；v3 作为长三角次级门户 seed 势能样板 |
| `xiamen_airport_system` | 厦门 | 翔安单机场 | 直接按厦门翔安国际机场作为当前经营对象，属于高崎迁建替换；v2 作为福建双核心 seed 势能样板 |
| `xian_airport_system` | 西安 | 咸阳单核心 | 以扩建和西北门户能力提升为主；v2 作为内陆枢纽竞争者 seed 势能样板 |
| `kunming_airport_system` | 昆明 | 长水单核心 | 以西南门户和东南亚连接扩容为主；v2 作为西南门户/东南亚连接 seed 势能样板 |
| `wuhan_airport_system` | 武汉 | 天河单核心 | 以中部枢纽扩建、高铁竞争约束为主；v2 作为内陆枢纽竞争者 seed 势能样板 |
| `zhengzhou_airport_system` | 郑州 | 新郑单核心 | 客货混合，保留货运强机场特征；v2 作为内陆枢纽竞争者 seed 势能样板 |
| `changsha_airport_system` | 长沙 | 黄花单核心 | 黄花改扩建/T3，适合测试中部休闲和商务客流增长；v2 作为中部成长省会 seed 势能样板 |
| `qingdao_airport_system` | 青岛 | 胶东单核心 | 已完成流亭到胶东的单机场替换，重点是容量爬坡和山东半岛门户；v2 作为沿海门户挑战者 seed 势能样板 |
| `tianjin_airport_system` | 天津 | 滨海单核心 | 京津冀副机场，适合测试强邻近枢纽挤压和外溢承接；v2 作为近首都外溢/压制 seed 势能样板 |
| `shijiazhuang_airport_system` | 石家庄 | 正定单核心 | 河北省会门户，适合测试京津强枢纽挤压下的腹地客流和低成本航线；v2 作为腹地低成本挑战者 seed 势能样板 |
| `jinan_airport_system` | 济南 | 遥墙单核心 | 山东内陆省会门户，以商务、省内腹地和扩建为主；v2 作为山东内陆门户 seed 势能样板 |
| `fuzhou_airport_system` | 福州 | 长乐单核心 | 与厦门形成福建双核心，处理省内分流和海峡门户属性；v2 作为福建双核心 seed 势能样板 |
| `shenyang_airport_system` | 沈阳 | 桃仙单核心 | 东北主门户之一，适合测试区域恢复、收缩和转机弱化；v2 作为东北恢复/承压门户 seed 势能样板 |
| `dalian_airport_system` | 大连 | 周水子单核心 | 预留大连金州湾国际机场，属于单机场迁建替换/海上新机场扩容；v2 作为东北沿海恢复门户 seed 势能样板 |
| `harbin_airport_system` | 哈尔滨 | 太平单核心 | 东北北部门户，冰雪旅游和俄远东连接特征明显；v2 作为东北恢复/承压补充 seed 势能样板 |
| `guiyang_airport_system` | 贵阳 | 龙洞堡单核心 | 西南内陆旅游和省会门户，适合测试山地省份航空依赖；v2 作为西南山地区域门户 seed 势能样板 |
| `nanning_airport_system` | 南宁 | 吴圩单核心 | 面向东盟的华南/西南连接节点；v2 作为面向东盟区域门户 seed 势能样板 |
| `haikou_airport_system` | 海口 | 美兰单核心 | 海南北部门户，和三亚形成岛内双核心；v2 作为海南北部门户/免税入口 seed 势能样板 |
| `sanya_airport_system` | 三亚 | 凤凰单核心 | 高休闲占比、高季节波动，适合压力测试旅游需求层；v2 作为海南高端旅游目的地 seed 势能样板 |
| `urumqi_airport_system` | 乌鲁木齐 | 地窝堡单核心 | 西北远程门户，适合测试长航线、地缘冲击和区域连接；v2 作为西北战略远程门户 seed 势能样板 |
| `hefei_airport_system` | 合肥 | 新桥单核心 | 新桥二期/T2，长三角内陆增长点，和南京、杭州、上海形成竞争；v2 作为长三角内陆增长挑战者 seed 势能样板 |
| `nanchang_airport_system` | 南昌 | 昌北单核心 | 昌北三期/T3，江西省会门户扩容；v2 作为普通省会追赶 seed 势能样板 |
| `ningbo_airport_system` | 宁波 | 栎社单核心 | 港口商务 + 长三角南翼机场，保留远期扩容槽位；v2 作为长三角港口制造挑战者 seed 势能样板 |
| `wenzhou_airport_system` | 温州 | 龙湾单核心 | 浙南民营经济/侨乡客流，商务、探亲和休闲混合；v2 作为长三角港口制造挑战者 seed 势能样板 |
| `changchun_airport_system` | 长春 | 龙嘉单核心 | 长春-吉林一体化，东北中部门户；v2 作为东北恢复/承压补充 seed 势能样板 |
| `taiyuan_airport_system` | 太原 | 武宿单核心 | 武宿三期/T3 + 二跑道，山西门户扩容；v2 作为普通省会追赶 seed 势能样板 |
| `lanzhou_airport_system` | 兰州 | 中川单核心 | 西北通道和甘青宁连接节点，适合测试长航线和弱中转；v2 作为西北通道门户 seed 势能样板 |
| `hohhot_airport_system` | 呼和浩特 | 盛乐单机场 | 直接按呼和浩特盛乐国际机场作为当前经营对象，属于白塔迁建替换；v2 作为西北/草原门户 seed 势能样板 |
| `yinchuan_airport_system` | 银川 | 河东单核心 | 宁夏门户，西北支线汇聚和旅游/商务混合；v2 作为西北区域门户 seed 势能样板 |
| `xining_airport_system` | 西宁 | 曹家堡单核心 | 青藏高原门户，特殊高原运营成本和天气约束；v2 作为高原门户约束 seed 势能样板 |
| `lhasa_airport_system` | 拉萨 | 贡嘎单核心 | 高原核心机场，海拔、天气和航线限制显著；v2 作为高原核心门户约束 seed 势能样板 |
| `zhuhai_airport_system` | 珠海 | 金湾单核心 | 大湾区西岸机场，受港澳广深挤压，旅游 + 商务分流；v2 作为湾区西岸外溢挑战者 seed 势能样板 |
| `quanzhou_jinjiang_airport_system` | 泉州/晋江 | 晋江单核心 | 闽南民营经济机场，和厦门翔安形成区域分流；v2 作为民营经济/侨乡挑战者 seed 势能样板 |
| `yantai_airport_system` | 烟台 | 蓬莱单核心 | 胶东半岛副门户，日韩/环渤海连接特征；v2 作为环渤海沿海副门户 seed 势能样板 |
| `wuxi_sunan_airport_system` | 无锡/苏州 | 苏南硕放单核心 | 苏南制造业机场，受上海、南京、杭州挤压，也承接商务补充需求；v2 作为长三角卫星挑战者 seed 势能样板 |
| `jieyang_chaoshan_airport_system` | 揭阳/潮汕 | 潮汕单核心 | 千万级潮汕都市圈机场，覆盖汕头、潮州、揭阳，商务、侨乡和探亲客流明显；v2 作为民营经济/侨乡挑战者 seed 势能样板 |
| `lijiang_airport_system` | 丽江 | 三义单核心 | 强旅游机场，高休闲占比和季节波动，适合测试旅游需求回落风险；v2 作为高弹性旅游目的地 seed 势能样板 |
| `xishuangbanna_airport_system` | 西双版纳 | 嘎洒单核心 | 云南热带旅游门户，休闲占比高，和昆明形成省内旅游分流；v2 作为高弹性旅游目的地 seed 势能样板 |
| `guilin_airport_system` | 桂林 | 两江单核心 | 老牌山水旅游门户，适合测试旅游目的地生命周期和高铁竞争；v2 作为老牌旅游生命周期 seed 势能样板 |
| `kashgar_airport_system` | 喀什 | 徕宁单核心 | 南疆门户机场，战略性强，适合测试远程支线、边疆连接和地缘冲击；v2 作为边疆战略门户挑战者 seed 势能样板 |

中国大陆当前纳入 ID：

```text
beijing_airport_system
shanghai_airport_system
guangzhou_airport_system
shenzhen_airport_system
chengdu_airport_system
chongqing_airport_system
hangzhou_airport_system
nanjing_airport_system
xiamen_airport_system
xian_airport_system
kunming_airport_system
wuhan_airport_system
zhengzhou_airport_system
changsha_airport_system
qingdao_airport_system
tianjin_airport_system
shijiazhuang_airport_system
jinan_airport_system
fuzhou_airport_system
shenyang_airport_system
dalian_airport_system
harbin_airport_system
guiyang_airport_system
nanning_airport_system
haikou_airport_system
sanya_airport_system
urumqi_airport_system
hefei_airport_system
nanchang_airport_system
ningbo_airport_system
wenzhou_airport_system
changchun_airport_system
taiyuan_airport_system
lanzhou_airport_system
hohhot_airport_system
yinchuan_airport_system
xining_airport_system
lhasa_airport_system
zhuhai_airport_system
quanzhou_jinjiang_airport_system
yantai_airport_system
wuxi_sunan_airport_system
jieyang_chaoshan_airport_system
lijiang_airport_system
xishuangbanna_airport_system
guilin_airport_system
kashgar_airport_system
```

中国大陆名称备注：

- 重庆：游戏内先用“重庆璧山机场”，括注“璧山正兴场址”即可。
- 杭州：游戏内先用“杭州第二机场”，括注“湖州德清方向传言/候选”；等正式选址或命名后再改。
- 南京：游戏内第一版按禄口单机场经营，不再预留第二机场自由选项；后续如果现实规划更清晰，再单独加入。
- 深圳：游戏内先用“惠州平潭机场（深圳第二机场功能）”表达协同供给，不使用玩家自由命名新机场。
- 上海：游戏内先用“南通新机场”，括注“南通市通州区二甲镇”，表达其长三角/上海航空枢纽溢出供给属性。
- 广州：游戏内先用“佛山高明机场”，括注“广州新机场/珠三角枢纽”，便于和白云机场区分。
- 厦门：游戏内直接使用“厦门翔安国际机场”作为当前经营对象，不再从高崎过渡。
- 大连：游戏内先用“大连金州湾国际机场”作为周水子替换项目，不按双机场处理。
- 石家庄：游戏内先用“石家庄正定机场”，重点不是全国枢纽竞争，而是河北省会门户、京津冀外溢和低成本航线空间。
- 呼和浩特：游戏内直接使用“呼和浩特盛乐国际机场”作为当前经营对象，不再从白塔过渡，不按双机场处理。
- 珠海：游戏内先以“珠海金湾机场”为客运经营对象；莲洲等通用机场先不计入客运机场瓶颈。
- 无锡/苏州：游戏内先用“苏南硕放机场”表达苏南都市圈补充机场，不单独拆无锡和苏州两个市场。
- 泉州/晋江：游戏内先用“泉州晋江机场”，强调闽南制造业、侨乡和厦门分流。
- 揭阳/潮汕：游戏内先用“潮汕机场”表达汕潮揭都市圈，不拆成单个城市。
- 丽江、西双版纳、桂林：虽然不是一线枢纽，但作为强旅游机场保留独立经营对象。
- 喀什：虽然规模低于千万级，但作为南疆门户和边疆战略机场保留独立经营对象。

## 日韩城市机场市场

日韩区域先纳入 9 个城市/都市圈机场市场。按当前主要客运机场计约 14 座；如果把釜山加德岛新机场、济州第二机场作为未来容量槽位，约 16 座。札幌丘珠等小型辅助机场先不作为独立经营对象。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `tokyo_airport_system` | 东京 | 羽田 + 成田，已是双机场 | 高密度双机场分工，适合测试国际/国内、商务/高端和时刻瓶颈 |
| `osaka_kansai_airport_system` | 大阪/关西 | 关西 + 伊丹 + 神户，三机场 | 关西国际门户 + 伊丹国内商务 + 神户补充容量 |
| `seoul_airport_system` | 首尔 | 仁川 + 金浦，已是双机场 | 仁川国际枢纽 + 金浦国内/短途商务，商业层价值高 |
| `busan_airport_system` | 釜山 | 金海单核心 | 预留加德岛新机场，作为金海替换/扩容和韩国南部门户 |
| `fukuoka_airport_system` | 福冈 | 福冈单核心 | 九州门户，高密度市区机场，重点是时刻、跑道和短途国际需求 |
| `sapporo_airport_system` | 札幌 | 新千岁单核心 | 北海道门户，冰雪旅游和国内休闲需求强；丘珠先不拆分 |
| `nagoya_airport_system` | 名古屋 | 中部 + 小牧 | 制造业商务机场系统，中部为主，小牧作为小型辅助机场 |
| `okinawa_naha_airport_system` | 冲绳/那霸 | 那霸单核心 | 旅游和离岛门户，先不拆宫古、石垣等离岛机场 |
| `jeju_airport_system` | 济州 | 济州单核心 | 预留济州第二机场（城山方向），强旅游和高拥堵压力 |

日韩当前纳入 ID：

```text
tokyo_airport_system
osaka_kansai_airport_system
seoul_airport_system
busan_airport_system
fukuoka_airport_system
sapporo_airport_system
nagoya_airport_system
okinawa_naha_airport_system
jeju_airport_system
```

日韩名称备注：

- 釜山：游戏内先用“加德岛新机场”作为未来容量槽位，当前仍以金海机场为主。
- 济州：游戏内先用“济州第二机场（城山方向）”作为规划槽位，现实争议和推进节奏可先简化。
- 札幌：新千岁是主经营对象；丘珠机场可作为说明背景，暂不单独建经营对象。
- 名古屋：中部机场是主经营对象，小牧机场保留为辅助容量和商务/区域航线背景。

## 东南亚城市机场市场

东南亚区域先纳入 10 个城市/都市圈机场市场。这个区域重点覆盖国家门户、旅游岛、廉航机场、拥堵首都机场和大型新机场规划。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `singapore_airport_system` | 新加坡 | 樟宜单核心 | 全球中转和高商业成熟度机场，适合测试高客单价、免税和转机消费 |
| `bangkok_airport_system` | 曼谷 | 素万那普 + 廊曼，已是双机场 | 素万那普国际枢纽 + 廊曼廉航/国内补充，旅游和价格敏感客流强 |
| `jakarta_airport_system` | 雅加达 | 苏加诺-哈达 + 哈利姆 | 印尼首都机场系统，拥堵、国内大盘和廉航需求明显 |
| `kuala_lumpur_airport_system` | 吉隆坡 | KLIA + 梳邦 | KLIA 国际/廉航枢纽 + 梳邦区域/商务补充 |
| `manila_airport_system` | 马尼拉 | 尼诺伊·阿基诺单核心 | 预留新马尼拉国际机场（布拉干），作为首都拥堵释放和新容量槽位 |
| `ho_chi_minh_airport_system` | 胡志明 | 新山一单核心 | 预留隆城国际机场，作为胡志明都市圈第二机场/长期扩容槽位 |
| `hanoi_airport_system` | 河内 | 内排单核心 | 越南北部门户，商务、政府和制造业客流增长 |
| `bali_denpasar_airport_system` | 巴厘/登巴萨 | 伍拉·赖单核心 | 强旅游岛机场，高休闲占比和季节/外部冲击敏感 |
| `phuket_airport_system` | 普吉 | 普吉单核心 | 强国际休闲目的地，适合测试旅游复苏、汇率和航司供给波动 |
| `surabaya_airport_system` | 泗水 | 朱安达单核心 | 印尼第二层级都市圈和东爪哇门户，国内大盘和商务/探亲混合 |
| `cebu_airport_system` | 宿务 | 麦克坦-宿务单核心 | 菲律宾第二门户，千万级客流，旅游、侨民和中转补充需求明显 |
| `da_nang_airport_system` | 岘港 | 岘港单核心 | 越南中部旅游和国际休闲门户，和河内、胡志明形成不同需求画像 |
| `chiang_mai_airport_system` | 清迈 | 清迈单核心 | 泰北旅游和区域生活方式机场，休闲、长住和价格敏感客流明显 |
| `medan_airport_system` | 棉兰 | 瓜拉纳穆单核心 | 苏门答腊门户，印尼西部区域商务、探亲和国内干线需求 |
| `penang_airport_system` | 槟城 | 槟城单核心 | 马来西亚北部制造业、医疗旅游和区域商务机场 |

东南亚当前纳入 ID：

```text
singapore_airport_system
bangkok_airport_system
jakarta_airport_system
kuala_lumpur_airport_system
manila_airport_system
ho_chi_minh_airport_system
hanoi_airport_system
bali_denpasar_airport_system
phuket_airport_system
surabaya_airport_system
cebu_airport_system
da_nang_airport_system
chiang_mai_airport_system
medan_airport_system
penang_airport_system
```

东南亚名称备注：

- 曼谷：游戏内用“素万那普 + 廊曼”表达双机场分工，素万那普偏国际枢纽，廊曼偏廉航和国内/区域航线。
- 马尼拉：游戏内先用“新马尼拉国际机场（布拉干）”作为未来容量槽位，当前仍以尼诺伊·阿基诺机场为瓶颈核心。
- 胡志明：游戏内先用“隆城国际机场”作为新容量槽位，新山一仍是当前主机场。
- 吉隆坡：KLIA 是主经营对象，梳邦保留为区域/商务辅助机场背景。
- 巴厘和普吉：虽然不是首都机场，但强旅游属性足够支撑独立经营对象。
- 宿务：游戏内先用“麦克坦-宿务机场”，作为菲律宾第二门户，不并入马尼拉市场。
- 岘港、清迈：虽然不是首都机场，但旅游和区域门户属性足够强，保留独立经营对象。
- 棉兰、槟城：规模略低于主干机场，但作为区域经济门户和商务/探亲市场保留。

## 南亚/印度城市机场市场

南亚/印度区域先纳入 12 个城市/都市圈机场市场。这个区域重点覆盖印度大城市扩容、新机场投放、价格敏感大盘、VFR/探亲流动、商务增长和巴基斯坦门户机场。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `delhi_airport_system` | 德里 | 英迪拉·甘地 + Noida/Jewar | 印度最大门户之一，Noida International Airport 作为德里 NCR 第二机场/新容量槽位 |
| `mumbai_airport_system` | 孟买 | 贾特拉帕蒂·希瓦吉 + Navi Mumbai | 金融和国际门户，Navi Mumbai International Airport 作为双机场扩容核心 |
| `bengaluru_airport_system` | 班加罗尔 | Kempegowda 单核心 | IT/商务增长机场，适合测试高增长商务和中高端消费 |
| `hyderabad_airport_system` | 海得拉巴 | Rajiv Gandhi 单核心 | 科技、医药和内陆航空增长节点，保留长期扩建槽位 |
| `chennai_airport_system` | 金奈 | Chennai 单核心 | 南…10996 tokens truncated…tem
san_juan_puerto_rico_airport_system
jamaica_airport_system
nassau_bahamas_airport_system
sao_paulo_airport_system
rio_de_janeiro_airport_system
brasilia_airport_system
belo_horizonte_airport_system
recife_airport_system
salvador_bahia_airport_system
fortaleza_airport_system
porto_alegre_airport_system
bogota_airport_system
medellin_airport_system
cartagena_airport_system
cali_airport_system
lima_airport_system
cusco_airport_system
santiago_chile_airport_system
buenos_aires_airport_system
cordoba_argentina_airport_system
mendoza_airport_system
quito_airport_system
guayaquil_airport_system
montevideo_airport_system
santa_cruz_bolivia_airport_system
```

拉美/加勒比名称备注：

- 墨西哥：墨西哥城按 Benito Juarez + Felipe Angeles + Toluca 表达多机场系统；坎昆/玛雅海岸把 Cancun 和 Tulum 作为同一旅游走廊供给；Guadalajara、Monterrey、Tijuana 保留为经济和边境主干。
- 中美洲：Panama City 是本区域最重要中转枢纽；San Jose、Liberia、San Salvador、Guatemala City 覆盖生态旅游、侨民/VFR、航司网络和国家门户。
- 加勒比：Punta Cana、Jamaica、Nassau 属于旅游例外；Santo Domingo 和 San Juan 更偏首都/区域门户。
- 巴西：Sao Paulo 按 Guarulhos + Congonhas + Viracopos 处理；Rio de Janeiro 按 Galeao + Santos Dumont 处理；Brasilia、Belo Horizonte、Recife、Salvador、Fortaleza、Porto Alegre 覆盖国内航空主干和区域门户。
- 安第斯/南锥体：Bogota、Lima、Santiago、Buenos Aires 是主干；Medellin、Cali、Quito、Guayaquil、Montevideo、Santa Cruz、Cordoba、Mendoza 补足区域经济和国内网络。
- 旅游例外口径：Cancun/Riviera Maya、Los Cabos、Puerto Vallarta、Liberia、Punta Cana、Jamaica、Nassau、Cartagena、Cusco 不是单纯按传统城市体量进入，而是用于测试旅游目的地冲击、季节性、机场商业和国际休闲航线。
- 暂不纳入：Havana/Varadero、Galapagos、Barbados、Aruba/Curacao、Bariloche、Florianopolis、Manaus、Asuncion、La Paz、Caracas 先放观察池。

## 北非城市机场市场

北非区域正式纳入 18 个城市/都市圈机场市场。这个区域按“欧洲旅游外溢 + 国家门户 + 红海/地中海旅游例外 + 中东/非洲连接 + 价格敏感增长市场”筛选，重点覆盖埃及、摩洛哥、阿尔及利亚和突尼斯。利比亚、苏丹等高不确定性或冲突恢复区域先不进入基础经营名单。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `cairo_airport_system` | 开罗 | Cairo 单核心 | 非洲最大机场之一，埃及国家门户，中东/非洲/欧洲连接和转机潜力强 |
| `hurghada_red_sea_airport_system` | 赫尔格达/红海 | Hurghada 单核心 | 超大型红海旅游目的地例外，欧洲休闲、包机和旺季容量压力明显 |
| `sharm_el_sheikh_airport_system` | 沙姆沙伊赫 | Sharm El Sheikh 单核心 | 西奈半岛旅游门户，欧洲/中东休闲客流和安全信心波动敏感 |
| `alexandria_airport_system` | 亚历山大 | Borg El Arab 单核心 | 埃及地中海门户，商务、侨民/VFR 和北岸旅游需求混合 |
| `luxor_airport_system` | 卢克索 | Luxor 单核心 | 尼罗河文化旅游门户，高旅游暴露和国际包机恢复弹性 |
| `marsa_alam_airport_system` | 马萨阿拉姆 | Marsa Alam 单核心 | 红海南部旅游例外，度假酒店、潜水旅游和欧洲包机需求明显 |
| `casablanca_airport_system` | 卡萨布兰卡 | Mohammed V 单核心 | 摩洛哥最大门户，Royal Air Maroc 枢纽、非洲/欧洲连接和商务需求 |
| `marrakech_airport_system` | 马拉喀什 | Marrakech Menara 单核心 | 超大型城市旅游门户，欧洲低成本航空和机场商业价值强 |
| `agadir_airport_system` | 阿加迪尔 | Agadir Al Massira 单核心 | 摩洛哥大西洋海滨旅游门户，度假需求和欧洲休闲客源明显 |
| `tangier_airport_system` | 丹吉尔 | Tangier Ibn Battouta 单核心 | 北摩洛哥港口/制造业门户，高铁和产业增长带动商务需求 |
| `rabat_airport_system` | 拉巴特 | Rabat-Sale 单核心 | 摩洛哥首都门户，政府公务、商务和区域增长 |
| `fes_airport_system` | 非斯 | Fes-Saiss 单核心 | 摩洛哥内陆文化旅游和侨民/VFR 门户，低成本航空需求稳定 |
| `algiers_airport_system` | 阿尔及尔 | Houari Boumediene 单核心 | 阿尔及利亚国家门户，能源经济、商务和法国/欧洲连接强 |
| `oran_airport_system` | 奥兰 | Ahmed Ben Bella 单核心 | 阿尔及利亚西部门户，港口、能源服务和侨民/VFR 需求 |
| `constantine_airport_system` | 君士坦丁 | Mohamed Boudiaf 单核心 | 阿尔及利亚东部门户，区域商务和国内干线需求 |
| `tunis_airport_system` | 突尼斯 | Tunis-Carthage 单核心 | 突尼斯国家门户，首都商务、欧洲连接和扩容压力 |
| `djerba_airport_system` | 杰尔巴 | Djerba-Zarzis 单核心 | 岛屿旅游目的地例外，欧洲休闲、包机和旺季波动明显 |
| `sahel_hammamet_airport_system` | 萨赫勒/哈马马特 | Monastir + Enfidha-Hammamet | 突尼斯海滨旅游走廊，双机场供给、包机和酒店需求强 |

北非当前纳入 ID：

```text
cairo_airport_system
hurghada_red_sea_airport_system
sharm_el_sheikh_airport_system
alexandria_airport_system
luxor_airport_system
marsa_alam_airport_system
casablanca_airport_system
marrakech_airport_system
agadir_airport_system
tangier_airport_system
rabat_airport_system
fes_airport_system
algiers_airport_system
oran_airport_system
constantine_airport_system
tunis_airport_system
djerba_airport_system
sahel_hammamet_airport_system
```

北非名称备注：

- 埃及：Cairo 是区域主门户；Hurghada、Sharm El Sheikh、Marsa Alam 按红海旅游例外处理；Alexandria 和 Luxor 分别覆盖地中海门户和文化旅游。
- 摩洛哥：Casablanca、Marrakech 是主干；Agadir、Tangier、Rabat、Fes 覆盖海滨旅游、港口制造、首都公务和文化/侨民需求。Casablanca 与 Marrakech 受机场扩建和 2030 前基础设施周期影响较大。
- 阿尔及利亚：Algiers、Oran、Constantine 进入正式名单；Annaba、Tlemcen、Setif、Bejaia 先放观察池。
- 突尼斯：Tunis 是国家门户；Djerba 和 Sahel/Hammamet 作为旅游走廊例外纳入，适合测试欧洲休闲需求、包机恢复和酒店周期。
- 暂不纳入：Tripoli/Mitiga、Benghazi、Misrata、Khartoum、Port Sudan、Nouakchott 先放观察池或恢复情景；如果后续需要表达冲突后恢复或撒哈拉/萨赫勒连接，再单独补。

## 大洋洲城市机场市场

大洋洲区域正式纳入 18 个城市/都市圈机场市场。这个区域按“高收入成熟市场 + 长途旅游 + 留学/探亲 + 资源周期 + 岛屿航空依赖 + 少数太平洋门户”筛选，重点覆盖澳大利亚、新西兰、斐济、巴布亚新几内亚和法属波利尼西亚。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `sydney_airport_system` | 悉尼 | Sydney + Western Sydney | 澳洲最大门户，现有机场容量/宵禁约束与 Western Sydney 新机场投放并存 |
| `melbourne_airport_system` | 墨尔本 | Melbourne + Avalon | 澳洲第二大城市机场系统，国际恢复、国内干线和 Avalon 低成本补充 |
| `brisbane_airport_system` | 布里斯班 | Brisbane 单核心 | 昆士兰主门户，国内干线、入境旅游和 2032 奥运前扩容周期明显 |
| `perth_airport_system` | 珀斯 | Perth 单核心 | 西澳资源经济门户，矿业 FIFO、长途国际线和印度洋连接价值强 |
| `adelaide_airport_system` | 阿德莱德 | Adelaide 单核心 | 南澳门户，商务、教育、葡萄酒旅游和国内干线需求稳定 |
| `gold_coast_airport_system` | 黄金海岸 | Gold Coast 单核心 | 超大型休闲目的地例外，低成本航空、家庭旅游和跨州休闲需求强 |
| `cairns_airport_system` | 凯恩斯 | Cairns 单核心 | 大堡礁和热带北昆士兰门户，国际休闲恢复和日本/亚洲航线敏感 |
| `canberra_airport_system` | 堪培拉 | Canberra 单核心 | 澳洲首都门户，政府公务、商务和区域连接需求 |
| `hobart_tasmania_airport_system` | 霍巴特/塔斯马尼亚 | Hobart 单核心 | 岛州门户，国内旅游、极地科考后勤和季节性需求增长 |
| `darwin_airport_system` | 达尔文 | Darwin 单核心 | 北澳门户，国防、资源、东南亚连接和远程航线战略价值 |
| `townsville_airport_system` | 汤斯维尔 | Townsville 单核心 | 北昆士兰区域门户，国防、资源服务和岛礁旅游补充 |
| `auckland_airport_system` | 奥克兰 | Auckland 单核心 | 新西兰最大国际门户，长途旅游、留学、移民/VFR 和跨太平洋连接 |
| `christchurch_airport_system` | 基督城 | Christchurch 单核心 | 新西兰南岛主门户，旅游、南极后勤和南岛区域连接 |
| `wellington_airport_system` | 惠灵顿 | Wellington 单核心 | 新西兰首都门户，政府公务、商务和国内干线需求 |
| `queenstown_airport_system` | 皇后镇 | Queenstown 单核心 | 超强旅游目的地例外，滑雪、湖区休闲和机场容量/地形约束明显 |
| `nadi_fiji_airport_system` | 楠迪/斐济 | Nadi 单核心 | 太平洋岛屿旅游和 Fiji Airways 区域枢纽，澳新/北美休闲航线强 |
| `port_moresby_airport_system` | 莫尔兹比港 | Jacksons 单核心 | 巴布亚新几内亚国家门户，资源经济、援助/公务和岛内航空依赖强 |
| `papeete_tahiti_airport_system` | 帕皮提/塔希提 | Faa'a 单核心 | 法属波利尼西亚远程旅游门户，高端海岛旅游和超长航线供给敏感 |

大洋洲当前纳入 ID：

```text
sydney_airport_system
melbourne_airport_system
brisbane_airport_system
perth_airport_system
adelaide_airport_system
gold_coast_airport_system
cairns_airport_system
canberra_airport_system
hobart_tasmania_airport_system
darwin_airport_system
townsville_airport_system
auckland_airport_system
christchurch_airport_system
wellington_airport_system
queenstown_airport_system
nadi_fiji_airport_system
port_moresby_airport_system
papeete_tahiti_airport_system
```

大洋洲名称备注：

- 澳大利亚：Sydney、Melbourne、Brisbane、Perth 是四个主干；Sydney 预留 Western Sydney 新机场作为新增供给；Melbourne 用 Avalon 表达低成本/次级机场补充。
- 澳大利亚区域门户：Adelaide、Canberra、Hobart、Darwin、Townsville 分别覆盖南澳、首都、塔斯马尼亚、北澳和北昆士兰；这些机场规模不一定都很大，但经营含义清晰。
- 澳大利亚旅游例外：Gold Coast 和 Cairns 进入正式名单，用于测试休闲需求、低成本航空、国际旅游恢复和季节性。
- 新西兰：Auckland、Christchurch、Wellington 是三大主干；Queenstown 作为旅游目的地例外纳入，适合测试容量、地形、天气和高客单价旅游。
- 太平洋门户：Nadi/Fiji、Port Moresby、Papeete/Tahiti 分别表达太平洋旅游枢纽、资源/国家门户和远程高端岛屿旅游。
- 暂不纳入：Sunshine Coast、Newcastle、Launceston、Hamilton、Dunedin、Nelson、Rarotonga、Apia、Noumea、Port Vila、Honiara 先放观察池；Noumea/New Caledonia 如后续需要表达政治扰动和恢复情景再单独补。

## 撒哈拉以南非洲城市机场市场

撒哈拉以南非洲区域正式纳入 38 个城市/都市圈机场市场。这个区域按“长期增长 + 航线不足 + 国家门户 + 非洲航司枢纽 + 资源/商务城市 + 旅游岛屿例外 + 容量追赶”筛选。北非已在 `north_africa` 单独处理；萨赫勒冲突带和恢复不确定性较高的机场先放观察池。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `johannesburg_airport_system` | 约翰内斯堡 | O.R. Tambo + Lanseria | 撒哈拉以南非洲最大门户之一，南非商务、区域中转和长途网络核心 |
| `cape_town_airport_system` | 开普敦 | Cape Town 单核心 | 南非第二门户，高端旅游、商务会展和长途国际恢复需求强 |
| `durban_airport_system` | 德班 | King Shaka 单核心 | 夸祖鲁-纳塔尔港口和海滨旅游门户，国内干线与区域商务混合 |
| `gqeberha_port_elizabeth_airport_system` | 格贝哈/伊丽莎白港 | Chief Dawid Stuurman 单核心 | 东开普制造业和海岸旅游门户，国内网络和商务需求稳定 |
| `addis_ababa_airport_system` | 亚的斯亚贝巴 | Bole 单核心 | Ethiopian Airlines 超级枢纽，非洲-亚洲-欧洲联程和新航站楼容量价值强 |
| `nairobi_airport_system` | 内罗毕 | Jomo Kenyatta + Wilson | 东非主门户，商务、货运、旅游和支线航空分工明显，扩容压力较高 |
| `mombasa_airport_system` | 蒙巴萨 | Moi 单核心 | 肯尼亚海岸旅游和港口门户，欧洲休闲、包机和区域贸易需求 |
| `dar_es_salaam_airport_system` | 达累斯萨拉姆 | Julius Nyerere 单核心 | 坦桑尼亚商业门户，国内增长、港口经济和区域连接需求强 |
| `zanzibar_airport_system` | 桑给巴尔 | Abeid Amani Karume 单核心 | 印度洋岛屿旅游例外，欧洲/中东休闲、酒店周期和季节性明显 |
| `kilimanjaro_arusha_airport_system` | 乞力马扎罗/阿鲁沙 | Kilimanjaro + Arusha | 野生动物旅游和登山门户，Safari/高端休闲需求强但容量较小 |
| `entebbe_kampala_airport_system` | 坎帕拉/恩德培 | Entebbe 单核心 | 乌干达国家门户，湖区经济、国际组织和东非区域连接 |
| `kigali_airport_system` | 基加利 | Kigali 单核心 | RwandAir 网络节点，预留 Bugesera 新机场作为长期枢纽扩容槽位 |
| `lagos_airport_system` | 拉各斯 | Murtala Muhammed 单核心 | 尼日利亚最大商业门户，商务、侨民/VFR、油气和供给瓶颈明显 |
| `abuja_airport_system` | 阿布贾 | Nnamdi Azikiwe 单核心 | 尼日利亚首都门户，政府公务、国内干线和区域商务需求 |
| `accra_airport_system` | 阿克拉 | Kotoka 单核心 | 加纳国家门户，西非商务、侨民/VFR 和航站楼扩容价值 |
| `abidjan_airport_system` | 阿比让 | Felix Houphouet-Boigny 单核心 | 法语西非商务门户，区域金融、港口经济和长途连接潜力 |
| `dakar_airport_system` | 达喀尔 | Blaise Diagne 单核心 | 西非大西洋门户，区域中转、侨民/VFR 和旅游增长 |
| `lome_airport_system` | 洛美 | Lome-Tokoin 单核心 | ASKY/Ethiopian 西非网络节点，小体量但中转和区域连接价值高 |
| `douala_yaounde_airport_system` | 杜阿拉/雅温得 | Douala + Yaounde Nsimalen | 喀麦隆经济首都 + 政治首都双门户，商务和中非连接需求 |
| `cotonou_airport_system` | 科托努 | Cadjehoun 单核心 | 贝宁国家门户，港口经济、尼日利亚外溢和区域商务需求 |
| `kinshasa_airport_system` | 金沙萨 | Ndjili 单核心 | 刚果（金）首都门户，超大城市潜在需求、收入约束和供给不足并存 |
| `lubumbashi_airport_system` | 卢本巴希 | Luano 单核心 | 铜钴矿业和赞比亚-刚果铜带门户，资源周期商务需求强 |
| `brazzaville_airport_system` | 布拉柴维尔 | Maya-Maya 单核心 | 刚果共和国首都门户，油气、政府公务和金沙萨跨河联系 |
| `libreville_airport_system` | 利伯维尔 | Leon-Mba 单核心 | 加蓬国家门户，油气商务、政府公务和中非连接 |
| `luanda_airport_system` | 罗安达 | Quatro de Fevereiro + Dr. Antonio Agostinho Neto | 安哥拉国家门户，新机场投放、油气商务和葡语非洲连接价值强 |
| `lusaka_airport_system` | 卢萨卡 | Kenneth Kaunda 单核心 | 赞比亚国家门户，铜带商务、区域连接和 Ethiopian 合作网络价值 |
| `harare_airport_system` | 哈拉雷 | Robert Gabriel Mugabe 单核心 | 津巴布韦国家门户，侨民/VFR、商务恢复和国内网络需求 |
| `maputo_airport_system` | 马普托 | Maputo 单核心 | 莫桑比克首都门户，天然气/港口经济、南非外溢和区域连接 |
| `windhoek_airport_system` | 温得和克 | Hosea Kutako + Eros | 纳米比亚国家门户，沙漠旅游、资源经济和小型国内机场分工 |
| `gaborone_airport_system` | 哈博罗内 | Sir Seretse Khama 单核心 | 博茨瓦纳首都门户，钻石/矿业商务和南非区域连接 |
| `mauritius_airport_system` | 毛里求斯 | Sir Seewoosagur Ramgoolam 单核心 | 印度洋高端旅游和金融门户，欧洲/印度/非洲连接价值强 |
| `seychelles_airport_system` | 塞舌尔 | Seychelles International 单核心 | 印度洋高端海岛旅游例外，高客单价、长途休闲和季节性明显 |
| `antananarivo_airport_system` | 塔那那利佛 | Ivato 单核心 | 马达加斯加国家门户，旅游、援助/公务和基础设施约束明显 |
| `cape_verde_airport_system` | 佛得角 | Praia + Sal + Boa Vista | 大西洋岛屿旅游和侨民门户，欧洲休闲、转机历史和季节性需求 |
| `banjul_senegambia_airport_system` | 班珠尔/塞内冈比亚 | Banjul 单核心 | 小体量旅游/VFR 例外，欧洲冬季度假和侨民需求明显 |
| `freetown_airport_system` | 弗里敦 | Freetown International 单核心 | 塞拉利昂国家门户，新航站楼、侨民/VFR 和恢复型商务需求 |
| `monrovia_airport_system` | 蒙罗维亚 | Roberts 单核心 | 利比里亚国家门户，侨民、NGO/援助和资源商务需求 |
| `lilongwe_airport_system` | 利隆圭 | Kamuzu 单核心 | 马拉维首都门户，小体量但承担国家连接和区域航空网络补点 |

撒哈拉以南非洲当前纳入 ID：

```text
johannesburg_airport_system
cape_town_airport_system
durban_airport_system
gqeberha_port_elizabeth_airport_system
addis_ababa_airport_system
nairobi_airport_system
mombasa_airport_system
dar_es_salaam_airport_system
zanzibar_airport_system
kilimanjaro_arusha_airport_system
entebbe_kampala_airport_system
kigali_airport_system
lagos_airport_system
abuja_airport_system
accra_airport_system
abidjan_airport_system
dakar_airport_system
lome_airport_system
douala_yaounde_airport_system
cotonou_airport_system
kinshasa_airport_system
lubumbashi_airport_system
brazzaville_airport_system
libreville_airport_system
luanda_airport_system
lusaka_airport_system
harare_airport_system
maputo_airport_system
windhoek_airport_system
gaborone_airport_system
mauritius_airport_system
seychelles_airport_system
antananarivo_airport_system
cape_verde_airport_system
banjul_senegambia_airport_system
freetown_airport_system
monrovia_airport_system
lilongwe_airport_system
```

撒哈拉以南非洲名称备注：

- 南部非洲：Johannesburg、Cape Town、Durban 是主干；Gqeberha、Windhoek、Gaborone、Maputo、Harare、Lusaka、Luanda 补足制造业、资源、港口和国家门户。
- 东非/非洲之角：Addis Ababa 和 Nairobi 是本区域最重要的枢纽；Dar es Salaam、Entebbe/Kampala、Kigali 补足国家门户；Mombasa、Zanzibar、Kilimanjaro/Arusha 按旅游走廊例外纳入。
- 西非：Lagos、Abuja、Accra、Abidjan、Dakar 是主干；Lome 因 ASKY/Ethiopian 网络节点属性保留；Cotonou、Banjul、Freetown、Monrovia 用于表达小国门户、侨民/VFR 和恢复型增长。
- 中非：Kinshasa、Lubumbashi、Douala/Yaounde、Brazzaville、Libreville 进入正式名单，用于表达超大潜在需求、资源商务、国家门户和供给不足。
- 印度洋/大西洋岛屿：Mauritius、Seychelles、Cape Verde 作为旅游/岛屿门户纳入；Antananarivo 作为马达加斯加国家门户纳入。
- 暂不纳入：Bamako、Ouagadougou、Niamey、N'Djamena、Mogadishu、Juba、Asmara、Malabo、Bata、Bujumbura、Blantyre、Maun、Victoria Falls、Zomba、Dodoma、Mwanza 先放观察池；其中部分可在安全恢复、旅游扩展或资源城市专题中补入。
