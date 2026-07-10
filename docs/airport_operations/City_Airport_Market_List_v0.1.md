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
| `chennai_airport_system` | 金奈 | Chennai 单核心 | 南印度制造业、港口和侨民/VFR 客流门户 |
| `kolkata_airport_system` | 加尔各答 | Netaji Subhas Chandra Bose 单核心 | 东印度门户，商务、探亲和区域连接混合 |
| `ahmedabad_airport_system` | 艾哈迈达巴德 | Sardar Vallabhbhai Patel 单核心 | 古吉拉特商务和侨民客流，适合测试区域经济增长 |
| `kochi_airport_system` | 科钦 | Cochin 单核心 | 喀拉拉侨民/VFR、海湾劳务和休闲旅游客流明显 |
| `goa_airport_system` | 果阿 | Dabolim + Manohar/Mopa | 双机场旅游市场，Manohar International Airport（Mopa）承接新增旅游容量 |
| `pune_airport_system` | 浦那 | Pune/Lohegaon 单核心 | 预留 Purandar 新机场，作为军民合用瓶颈释放和商务增长槽位 |
| `islamabad_rawalpindi_airport_system` | 伊斯兰堡/拉瓦尔品第 | Islamabad International 单核心 | 巴基斯坦首都门户，政府、商务和探亲客流 |
| `karachi_airport_system` | 卡拉奇 | Jinnah 单核心 | 巴基斯坦最大商业城市门户，商务、侨民和海湾连接明显 |
| `dhaka_airport_system` | 达卡 | Hazrat Shahjalal 单核心 | 孟加拉国最大门户，劳务/VFR、商务和容量压力明显 |
| `colombo_airport_system` | 科伦坡 | Bandaranaike 单核心 | 斯里兰卡国家门户，旅游、劳务/VFR 和区域中转恢复 |
| `male_airport_system` | 马累 | Velana 单核心 | 马尔代夫旅游门户，高国际休闲占比和高商业客单价潜力 |
| `kathmandu_airport_system` | 加德满都 | Tribhuvan 单核心 | 尼泊尔核心国际门户，山地天气、旅游、劳务和容量约束明显 |

南亚/印度当前纳入 ID：

```text
delhi_airport_system
mumbai_airport_system
bengaluru_airport_system
hyderabad_airport_system
chennai_airport_system
kolkata_airport_system
ahmedabad_airport_system
kochi_airport_system
goa_airport_system
pune_airport_system
islamabad_rawalpindi_airport_system
karachi_airport_system
dhaka_airport_system
colombo_airport_system
male_airport_system
kathmandu_airport_system
```

南亚/印度名称备注：

- 德里：游戏内先用“Noida International Airport（Jewar）”表达德里 NCR 第二机场和新供给释放。
- 孟买：游戏内先用“Navi Mumbai International Airport”表达双机场扩容，和既有孟买机场共同构成都会区瓶颈。
- 果阿：游戏内按 Dabolim + Manohar International Airport（Mopa）双机场旅游市场处理。
- 浦那：游戏内先用“Purandar 新机场”作为远期规划槽位，当前仍以 Pune/Lohegaon 的军民合用瓶颈为主。
- 科钦、卡拉奇、伊斯兰堡/拉瓦尔品第：重点不是超级中转，而是 VFR、劳务/侨民和区域门户。
- 达卡：游戏内先用 Hazrat Shahjalal 机场，强调劳务/VFR 大盘和航站楼容量压力。
- 科伦坡、马累、加德满都：虽然经济体量不如印度大城市，但作为国家门户和旅游/劳务连接点保留独立经营对象。
- 拉合尔：先放观察池，暂不进入本轮名单；如后续需要补巴基斯坦第二门户再加入。

## 港澳台城市机场市场

港澳台区域先纳入 4 个城市/都市圈机场市场。这个区域机场数量少，但国际客、高端客、免税、精品零售和两岸/区域短途航线价值高。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `hong_kong_airport_system` | 香港 | 香港国际单核心 | 三跑道系统，高国际/中转/货运/高端商业属性，适合测试高客单价机场商业 |
| `macau_airport_system` | 澳门 | 澳门国际单核心 | 博彩旅游和大湾区短途国际门户，规模中等但商业和旅游属性突出 |
| `taipei_airport_system` | 台北 | 桃园 + 松山，已是双机场 | 桃园国际门户 + 松山市区商务/区域航线，适合测试双机场分工 |
| `kaohsiung_airport_system` | 高雄 | 小港单核心 | 台湾南部门户，旅游、商务和区域短途国际航线 |

港澳台当前纳入 ID：

```text
hong_kong_airport_system
macau_airport_system
taipei_airport_system
kaohsiung_airport_system
```

港澳台名称备注：

- 香港：游戏内先用“香港国际机场”作为单机场系统，但容量项目写“三跑道系统”，不拆第二机场。
- 澳门：虽然规模低于千万级，但作为独立经济体门户和旅游/博彩消费机场保留。
- 台北：桃园是主国际门户，松山作为市区商务和短途区域机场，不单独拆市场。
- 高雄：作为台湾南部门户保留；台中、花莲、台东等先不进入第一轮经营层。

## 中东/海湾城市机场市场

中东/海湾区域先纳入 12 个稳定运营的城市/都市圈机场市场。这个区域重点覆盖海湾超级中转、沙特宗教门户、油气商务、高端免税/奢侈消费和长途联程网络。处于冲突或高恢复不确定性的机场先不进入本轮名单。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `dubai_airport_system` | 迪拜 | DXB + Al Maktoum/DWC | DXB 超级中转枢纽 + Al Maktoum/DWC 远期巨型扩容槽位 |
| `sharjah_airport_system` | 沙迦 | Sharjah 单核心 | 阿联酋北部和低成本/区域航线门户，和迪拜形成错位补充 |
| `doha_airport_system` | 多哈 | Hamad 单核心 | 全球长途中转和高端商业机场，强依赖国际联程网络 |
| `abu_dhabi_airport_system` | 阿布扎比 | Zayed 单核心 | 阿联酋第二国际门户，Etihad 枢纽和高端商务/休闲增长 |
| `riyadh_airport_system` | 利雅得 | King Khalid 单核心 | 预留 King Salman International Airport，作为沙特首都新全球枢纽槽位 |
| `jeddah_airport_system` | 吉达 | King Abdulaziz 单核心 | 红海门户和朝觐/副朝主入口，宗教客流峰值强 |
| `medina_airport_system` | 麦地那 | Prince Mohammad bin Abdulaziz 单核心 | 宗教客流门户，和吉达共同承接朝觐/副朝航空需求 |
| `dammam_airport_system` | 达曼/东部省 | King Fahd 单核心 | 沙特东部油气商务、海湾区域连接和工业腹地 |
| `muscat_airport_system` | 马斯喀特 | Muscat 单核心 | 阿曼门户，区域连接、旅游和地缘绕行弹性较强 |
| `kuwait_city_airport_system` | 科威特城 | Kuwait 单核心 | 科威特国家门户，油气商务、VFR 和区域航线 |
| `bahrain_airport_system` | 巴林/麦纳麦 | Bahrain 单核心 | 海湾金融、货运和短途区域门户，规模中等但枢纽历史强 |
| `amman_airport_system` | 安曼 | Queen Alia 单核心 | 约旦国家门户，黎凡特稳定入口、旅游、VFR 和区域中转 |

中东/海湾当前纳入 ID：

```text
dubai_airport_system
sharjah_airport_system
doha_airport_system
abu_dhabi_airport_system
riyadh_airport_system
jeddah_airport_system
medina_airport_system
dammam_airport_system
muscat_airport_system
kuwait_city_airport_system
bahrain_airport_system
amman_airport_system
```

中东/海湾名称备注：

- 区域边界：本轮按 Gulf + Saudi + Jordan 处理；Turkey 已归入 `central_asia_turkey_eurasia`，North Africa 另有 `north_africa`。
- 迪拜：游戏内用 DXB + Al Maktoum/DWC 表达当前超级枢纽和未来巨型容量迁移。
- 利雅得：游戏内先用 King Salman International Airport 作为远期新全球枢纽槽位，当前仍以 King Khalid 为主。
- 吉达、麦地那：按宗教客流门户处理，朝觐/副朝峰值可以作为机场经营层的特殊需求周期。
- 沙迦：虽然和迪拜地理接近，但规模和低成本/区域航线特征足够清晰，先单独保留。
- 安曼：作为稳定黎凡特门户保留；Tel Aviv、Tehran、Baghdad、Beirut、Damascus/Aleppo、Sana'a/Aden 等先放观察池或恢复情景，不进入本轮经营名单。

## 中亚/土耳其/欧亚桥城市机场市场

中亚/土耳其/欧亚桥区域先纳入 13 个城市/都市圈机场市场。这个区域按“千万级左右 + 欧亚桥战略功能”筛选：土耳其保留千万级大盘和旅游组合，中亚/高加索则保留国家门户、航路绕行和区域增长节点。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `istanbul_airport_system` | 伊斯坦布尔 | Istanbul + Sabiha Gokcen，已是双机场 | 欧亚超级中转枢纽，长途联程、商务、高端和低成本客流并存 |
| `antalya_airport_system` | 安塔利亚 | Antalya 单核心 | 土耳其地中海强旅游机场，国际休闲、包机和季节性压力明显 |
| `ankara_airport_system` | 安卡拉 | Esenboga 单核心 | 土耳其首都门户，三跑道/扩建后可测试高铁竞争下的航空恢复 |
| `izmir_airport_system` | 伊兹密尔 | Adnan Menderes 单核心 | 爱琴海门户，城市商务、侨民/VFR 和休闲旅游混合 |
| `mugla_resort_airport_system` | 穆拉/爱琴海度假区 | Dalaman + Milas-Bodrum | 两机场组合接近千万级旅游市场，适合测试欧洲休闲客和季节性 |
| `cukurova_airport_system` | 阿达纳/梅尔辛/Çukurova | Çukurova 单核心 | 新机场替换 Adana/Mersin 区域门户，工业、农业和东地中海连接 |
| `almaty_airport_system` | 阿拉木图 | Almaty 单核心 | 哈萨克斯坦最大商业门户，中亚最强航空节点之一，远期大扩容 |
| `astana_airport_system` | 阿斯塔纳 | Nursultan Nazarbayev 单核心 | 哈萨克斯坦首都门户，接近千万级，国内干线和国际增长并重 |
| `tashkent_airport_system` | 塔什干 | Islam Karimov 单核心 | 乌兹别克斯坦国家门户，接近千万级，丝路旅游和区域中转增长 |
| `baku_airport_system` | 巴库 | Heydar Aliyev 单核心 | 里海/高加索能源商务门户，区域中转、货运和地缘绕行价值高 |
| `tbilisi_airport_system` | 第比利斯 | Tbilisi 单核心 | 格鲁吉亚国家门户，旅游、VFR 和高加索走廊需求明显 |
| `yerevan_airport_system` | 埃里温 | Zvartnots 单核心 | 亚美尼亚国家门户，侨民/VFR、旅游和机场扩建需求明显 |
| `bishkek_airport_system` | 比什凯克 | Manas 单核心 | 吉尔吉斯斯坦门户，规模低于千万但承担中亚支点、劳务/VFR 和旅游连接 |

中亚/土耳其/欧亚桥当前纳入 ID：

```text
istanbul_airport_system
antalya_airport_system
ankara_airport_system
izmir_airport_system
mugla_resort_airport_system
cukurova_airport_system
almaty_airport_system
astana_airport_system
tashkent_airport_system
baku_airport_system
tbilisi_airport_system
yerevan_airport_system
bishkek_airport_system
```

中亚/土耳其/欧亚桥名称备注：

- 伊斯坦布尔：游戏内用 Istanbul Airport + Sabiha Gokcen 表达双机场系统，不拆成两个城市市场。
- 穆拉/爱琴海度假区：Dalaman 和 Milas-Bodrum 单独看都不到千万级，但组合起来是清晰的旅游机场市场。
- Çukurova：游戏内作为 Adana/Mersin 区域替换机场和新供给槽位，不再单列旧 Adana 机场。
- 阿拉木图、阿斯塔纳、塔什干：按中亚主干门户处理，是本区域机场经营层的核心。
- 巴库、第比利斯、埃里温：规模多在 500-800 万级，但作为高加索国家门户和地缘绕行节点保留。
- 比什凯克：严格规模低于主门槛，但作为吉尔吉斯斯坦门户和中亚补点保留；Samarkand、Batumi、Aktau、Dushanbe、Ashgabat 先放观察池。

## 南欧/东欧/地中海城市机场市场

南欧/东欧/地中海区域正式纳入 32 个城市/都市圈机场市场。这个区域改用“传统城市/首都/区域经济中心优先 + 超大型旅游目的地例外”的口径：普通旅游机场不默认进入基础经营名单，但体量特别大、机场商业价值高、季节性容量压力明显的目的地可以作为独立经营对象。法国、德国、英国、荷兰、瑞士、奥地利、北欧和爱尔兰先留给 `west_north_europe`；土耳其已经归入 `central_asia_turkey_eurasia`。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `madrid_airport_system` | 马德里 | Barajas 单核心 | 西班牙最大门户，商务、拉美连接和货运能力强 |
| `barcelona_airport_system` | 巴塞罗那 | El Prat 单核心 | 地中海大城市门户，商务、旅游和低成本航空混合 |
| `balearic_islands_airport_system` | 巴利阿里群岛 | Palma + Ibiza + Menorca | 超大型旅游目的地例外，旺季容量、廉航和机场商业压力都很强 |
| `valencia_airport_system` | 瓦伦西亚 | Valencia 单核心 | 地中海城市门户，商务、休闲和会展需求混合 |
| `seville_airport_system` | 塞维利亚 | Seville 单核心 | 安达卢西亚首府门户，接近千万级，城市旅游和区域商务混合 |
| `bilbao_airport_system` | 毕尔巴鄂 | Bilbao 单核心 | 巴斯克地区门户，工业、商务和北西班牙区域需求 |
| `malaga_costa_del_sol_airport_system` | 马拉加 | Malaga-Costa del Sol 单核心 | 体量很大但旅游占比高，作为城市型旅游门户保留 |
| `alicante_costa_blanca_airport_system` | 阿利坎特/白色海岸 | Alicante-Elche 单核心 | 超大型旅游目的地例外，欧洲休闲、退休旅居和 VFR 客流很强 |
| `canary_islands_airport_system` | 加那利群岛 | Gran Canaria + Tenerife South/North + Lanzarote/Fuerteventura | 超大型旅游目的地例外，远程休闲、岛屿民生和季节波动都明显 |
| `lisbon_airport_system` | 里斯本 | Humberto Delgado 单核心 | 预留 Luis de Camoes Airport（Alcochete），解决首都机场容量瓶颈 |
| `porto_airport_system` | 波尔图 | Francisco Sa Carneiro 单核心 | 葡萄牙北部门户，侨民/VFR、旅游和商务混合 |
| `rome_airport_system` | 罗马 | Fiumicino + Ciampino | 意大利最大门户，长途、旅游、宗教和低成本机场分工 |
| `milan_lombardy_airport_system` | 米兰/伦巴第 | Malpensa + Linate + Bergamo | 北意商务、低成本和长途门户三机场系统 |
| `venice_airport_system` | 威尼斯 | Marco Polo 单核心 | 高旅游密度，但仍是东北意大利城市门户 |
| `naples_airport_system` | 那不勒斯 | Capodichino 单核心 | 南意城市和坎帕尼亚旅游门户，机场扩容压力明显 |
| `bologna_airport_system` | 博洛尼亚 | Guglielmo Marconi 单核心 | 北意制造业、会展和低成本航空节点 |
| `bari_puglia_airport_system` | 巴里/普利亚 | Bari 单核心 | 亚得里亚海门户，南意旅游、侨民和区域商务增长 |
| `catania_airport_system` | 卡塔尼亚 | Catania-Fontanarossa 单核心 | 西西里东部最大城市机场，旅游和区域民生客流并存 |
| `athens_airport_system` | 雅典 | Athens 单核心 | 希腊国家门户，城市旅游、爱琴海转接和商务需求 |
| `crete_airport_system` | 克里特 | Heraklion + Chania | 超大型旅游目的地例外，Heraklion 新机场/扩容可作为远期供给槽位 |
| `thessaloniki_airport_system` | 塞萨洛尼基 | Thessaloniki 单核心 | 希腊北部门户，巴尔干连接和休闲需求混合 |
| `cyprus_airport_system` | 塞浦路斯 | Larnaca + Paphos | 超大型岛屿旅游 + 国家门户例外，旅游、VFR 和中东/欧洲连接明显 |
| `malta_airport_system` | 马耳他 | Malta 单核心 | 小经济体国家门户例外，旅游、语言教育、低成本航空和商业消费强 |
| `warsaw_airport_system` | 华沙 | Chopin + Modlin | 波兰最大门户，LOT 枢纽、低成本补充和远期 CPK 槽位 |
| `krakow_airport_system` | 克拉科夫 | John Paul II 单核心 | 波兰最大区域机场之一，旅游、商务和低成本航空增长强 |
| `prague_airport_system` | 布拉格 | Vaclav Havel 单核心 | 捷克国家门户，城市旅游和中欧商务需求 |
| `budapest_airport_system` | 布达佩斯 | Ferenc Liszt 单核心 | 匈牙利国家门户，低成本、旅游和区域商务增长强 |
| `bucharest_airport_system` | 布加勒斯特 | Henri Coanda + Baneasa | 罗马尼亚首都机场系统，Henri Coanda 为主，Baneasa 作辅助 |
| `belgrade_airport_system` | 贝尔格莱德 | Nikola Tesla 单核心 | 塞尔维亚国家门户，巴尔干区域中转和侨民/VFR 明显 |
| `sofia_airport_system` | 索菲亚 | Sofia 单核心 | 保加利亚国家门户，低成本航空和区域商务增长 |
| `tirana_airport_system` | 地拉那 | Tirana 单核心 | 阿尔巴尼亚快速增长门户，旅游、侨民/VFR 和低成本航空突出 |
| `zagreb_airport_system` | 萨格勒布 | Franjo Tudman 单核心 | 克罗地亚首都门户，商务、国家连接和货运背景 |

南欧/东欧/地中海当前纳入 ID：

```text
madrid_airport_system
barcelona_airport_system
balearic_islands_airport_system
valencia_airport_system
seville_airport_system
bilbao_airport_system
malaga_costa_del_sol_airport_system
alicante_costa_blanca_airport_system
canary_islands_airport_system
lisbon_airport_system
porto_airport_system
rome_airport_system
milan_lombardy_airport_system
venice_airport_system
naples_airport_system
bologna_airport_system
bari_puglia_airport_system
catania_airport_system
athens_airport_system
crete_airport_system
thessaloniki_airport_system
cyprus_airport_system
malta_airport_system
warsaw_airport_system
krakow_airport_system
prague_airport_system
budapest_airport_system
bucharest_airport_system
belgrade_airport_system
sofia_airport_system
tirana_airport_system
zagreb_airport_system
```

南欧/东欧/地中海名称备注：

- 体量判断：南欧旅游机场确实很大，例如 Palma、Malaga、Alicante、Gran Canaria、Tenerife South 都能达到千万级左右或以上；但正式经营名单不再只按客流体量选，而是优先城市经济、腹地稳定性、长期容量瓶颈和少数超大型旅游例外。
- 西班牙：马德里、巴塞罗那、瓦伦西亚、塞维利亚、毕尔巴鄂按传统城市门户处理；马拉加因体量足够大且有明确城市腹地，保留在正式名单。
- 西班牙超大型旅游例外：Balearic Islands、Alicante/Costa Blanca、Canary Islands 纳入正式名单，用于承接旅游旺季、低成本航空、商业消费和容量压力。
- 葡萄牙：里斯本保留 Luis de Camoes Airport（Alcochete）远期槽位；波尔图作为北部门户；Faro/Algarve 先放旅游观察池。
- 意大利：米兰按 Malpensa + Linate + Bergamo 三机场系统；罗马、威尼斯、那不勒斯、博洛尼亚、巴里、卡塔尼亚按城市门户处理；Sardinia、Palermo、Olbia 先放观察池。
- 希腊：雅典和塞萨洛尼基进入传统城市名单；Crete 作为超大型旅游目的地例外纳入；Rhodes、Corfu、Santorini、Kos 先放旅游观察池。
- 小岛国家/区域：Cyprus、Malta 以“岛屿国家门户 + 高旅游商业价值”的例外口径纳入正式名单。
- 中东欧：华沙、克拉科夫、布拉格、布达佩斯、布加勒斯特是本区域东欧/中欧主干；维也纳先归入 `west_north_europe`。
- 巴尔干：贝尔格莱德、索菲亚、地拉那、萨格勒布先入表；Croatian Adriatic、Sarajevo、Skopje、Podgorica、Ljubljana、Chisinau 先放观察池。
- 冲突/制裁或数据不稳定区域：Ukraine、Russia、Belarus 暂不进入本轮机场经营名单。

## 西欧/北欧城市机场市场

西欧/北欧区域正式纳入 39 个城市/都市圈机场市场。这个区域按“成熟航空市场 + 多机场分工 + 高成本/环保约束 + 商务/旅游混合 + 少数季节性旅游例外”筛选，适合测试容量瓶颈、高铁竞争、机场商业成熟度、低成本航空外溢和冬夏季旅游峰值。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `london_airport_system` | 伦敦 | Heathrow + Gatwick + Stansted + Luton + City | 欧洲最大多机场系统，长途枢纽、低成本外溢和容量扩张争议并存 |
| `manchester_airport_system` | 曼彻斯特 | Manchester 单核心 | 英格兰北部门户，长途增长、区域商务和休闲出境需求强 |
| `birmingham_airport_system` | 伯明翰 | Birmingham 单核心 | 英格兰中部门户，制造业、族裔/VFR 和价格敏感客流混合 |
| `edinburgh_airport_system` | 爱丁堡 | Edinburgh 单核心 | 苏格兰首府门户，旅游、商务和跨大西洋增长潜力明显 |
| `glasgow_airport_system` | 格拉斯哥 | Glasgow 单核心 | 苏格兰西部门户，探亲、休闲和区域商务需求 |
| `bristol_airport_system` | 布里斯托 | Bristol 单核心 | 英格兰西南门户，休闲出境和区域腹地稳定 |
| `belfast_airport_system` | 贝尔法斯特 | Belfast International + Belfast City | 北爱尔兰双机场系统，低成本、英国国内和城市商务分工 |
| `dublin_airport_system` | 都柏林 | Dublin 单核心 | 爱尔兰国家门户，跨大西洋、低成本和科技商务需求强 |
| `paris_airport_system` | 巴黎 | Charles de Gaulle + Orly + Beauvais | 欧洲级双核心枢纽，长途、精品商业、低成本外溢和高铁竞争并存 |
| `nice_cote_d_azur_airport_system` | 尼斯/蔚蓝海岸 | Nice 单核心 | 高端旅游 + 商务会展门户，商业客单价和季节性都强 |
| `lyon_airport_system` | 里昂 | Lyon-Saint Exupery 单核心 | 法国东南部商务、制造业和阿尔卑斯入口门户 |
| `marseille_airport_system` | 马赛 | Marseille Provence 单核心 | 法国南部港口城市门户，地中海、北非和低成本航空需求强 |
| `toulouse_airport_system` | 图卢兹 | Toulouse-Blagnac 单核心 | 航空制造业城市门户，商务客流和欧洲干线需求稳定 |
| `bordeaux_airport_system` | 波尔多 | Bordeaux-Merignac 单核心 | 西南法门户，城市旅游、葡萄酒旅游和区域商务混合 |
| `nantes_airport_system` | 南特 | Nantes Atlantique 单核心 | 法国西部门户，区域经济、休闲和机场扩容争议 |
| `corsica_airport_system` | 科西嘉 | Ajaccio + Bastia + Figari + Calvi | 季节性旅游例外，岛屿民生、法国内陆连接和旺季容量压力明显 |
| `frankfurt_rhine_main_airport_system` | 法兰克福/莱茵-美因 | Frankfurt 单核心 | 欧洲级长途和货运枢纽，商务、转机和货运能力强 |
| `munich_airport_system` | 慕尼黑 | Munich 单核心 | 德国南部枢纽，长途增长、商务和高端消费需求强 |
| `berlin_airport_system` | 柏林 | Berlin Brandenburg 单核心 | 德国首都门户，政治、商务、旅游和低成本航空混合 |
| `rhine_ruhr_airport_system` | 莱茵-鲁尔 | Dusseldorf + Cologne/Bonn + Dortmund | 德国最大都市圈多机场系统，商务、低成本和货运分工明显 |
| `hamburg_airport_system` | 汉堡 | Hamburg 单核心 | 德国北部门户，商务、会展和港口经济客流 |
| `stuttgart_airport_system` | 斯图加特 | Stuttgart 单核心 | 德国西南制造业门户，汽车产业商务和欧洲干线需求 |
| `amsterdam_airport_system` | 阿姆斯特丹 | Schiphol 单核心 | 欧洲级中转枢纽，容量/噪音约束、货运和商业消费都重要 |
| `brussels_airport_system` | 布鲁塞尔 | Brussels + Charleroi | 欧盟首都门户 + 低成本外溢，商务、外交和廉航分工清晰 |
| `luxembourg_airport_system` | 卢森堡 | Luxembourg 单核心 | 小经济体金融门户，客运规模中等但货运和商务属性强 |
| `zurich_airport_system` | 苏黎世 | Zurich 单核心 | 瑞士最大门户，高端商务、金融和长途联程价值高 |
| `geneva_airport_system` | 日内瓦 | Geneva 单核心 | 国际组织/商务 + 阿尔卑斯滑雪入口，季节性和高端客流并存 |
| `basel_euro_airport_system` | 巴塞尔/米卢斯/弗赖堡 | EuroAirport 单核心 | 跨境机场，瑞士/法国/德国三地腹地和低成本航空需求 |
| `vienna_airport_system` | 维也纳 | Vienna 单核心 | 中欧门户，东欧连接、长途增长和高商业成熟度 |
| `salzburg_innsbruck_alps_airport_system` | 萨尔茨堡/因斯布鲁克 | Salzburg + Innsbruck | 季节性旅游例外，阿尔卑斯滑雪、包机和冬季容量压力突出 |
| `copenhagen_airport_system` | 哥本哈根 | Copenhagen 单核心 | 北欧门户，SAS 枢纽、商务、转机和邮轮/休闲需求混合 |
| `stockholm_airport_system` | 斯德哥尔摩 | Arlanda + Bromma | 瑞典首都机场系统，商务、国内干线和北欧连接 |
| `oslo_airport_system` | 奥斯陆 | Gardermoen 单核心 | 挪威国家门户，国内航空依赖、能源商务和北欧连接强 |
| `helsinki_airport_system` | 赫尔辛基 | Helsinki-Vantaa 单核心 | 芬兰国家门户，亚欧连接弱化后仍保留北欧/波罗的海枢纽价值 |
| `gothenburg_airport_system` | 哥德堡 | Landvetter 单核心 | 瑞典西部门户，制造业、港口和区域商务需求 |
| `bergen_airport_system` | 卑尔根 | Bergen 单核心 | 挪威西部门户，峡湾旅游、能源商务和国内航空依赖 |
| `reykjavik_keflavik_airport_system` | 雷克雅未克/凯夫拉维克 | Keflavik + Reykjavik Domestic | 冰岛旅游 + 北大西洋连接，国际门户和国内支线分工 |
| `tromso_arctic_airport_system` | 特罗姆瑟 | Tromso 单核心 | 季节性旅游例外，北极/极光旅游和国际冬季航线增长明显 |
| `lapland_airport_system` | 拉普兰 | Rovaniemi + Kittila + Ivalo | 季节性旅游例外，圣诞、极光、包机和冬季机场商业峰值突出 |

西欧/北欧当前纳入 ID：

```text
london_airport_system
manchester_airport_system
birmingham_airport_system
edinburgh_airport_system
glasgow_airport_system
bristol_airport_system
belfast_airport_system
dublin_airport_system
paris_airport_system
nice_cote_d_azur_airport_system
lyon_airport_system
marseille_airport_system
toulouse_airport_system
bordeaux_airport_system
nantes_airport_system
corsica_airport_system
frankfurt_rhine_main_airport_system
munich_airport_system
berlin_airport_system
rhine_ruhr_airport_system
hamburg_airport_system
stuttgart_airport_system
amsterdam_airport_system
brussels_airport_system
luxembourg_airport_system
zurich_airport_system
geneva_airport_system
basel_euro_airport_system
vienna_airport_system
salzburg_innsbruck_alps_airport_system
copenhagen_airport_system
stockholm_airport_system
oslo_airport_system
helsinki_airport_system
gothenburg_airport_system
bergen_airport_system
reykjavik_keflavik_airport_system
tromso_arctic_airport_system
lapland_airport_system
```

西欧/北欧名称备注：

- 英国/爱尔兰：伦敦按五机场都市圈处理；Manchester、Birmingham、Edinburgh、Glasgow、Bristol、Belfast、Dublin 覆盖英国/爱尔兰主要区域门户。Liverpool、Newcastle、Leeds Bradford、East Midlands、Cork、Shannon 先放观察池。
- 法国：巴黎按 CDG + Orly + Beauvais 处理；Nice、Lyon、Marseille、Toulouse、Bordeaux、Nantes 进入正式名单；Corsica 作为岛屿旅游例外纳入。Montpellier、Strasbourg、Lille、Rennes、Corsica 内部单机场拆分先不做。
- 德国：Frankfurt、Munich、Berlin 是主干；Rhine-Ruhr 用 Dusseldorf + Cologne/Bonn + Dortmund 表达大都市圈分工；Hamburg、Stuttgart 保留。Hanover、Nuremberg、Bremen、Dresden、Leipzig/Halle、Memmingen 先放观察池或货运/低成本情景。
- 荷比卢：Amsterdam 是核心；Brussels + Charleroi 表达首都门户和低成本外溢；Luxembourg 客运规模中等，但金融商务和货运属性强。
- 瑞士/奥地利：Zurich、Geneva、Basel、Vienna 进入正式名单；Salzburg + Innsbruck 作为阿尔卑斯季节性旅游例外纳入。
- 北欧/冰岛：Copenhagen、Stockholm、Oslo、Helsinki 是国家/区域门户；Gothenburg、Bergen、Reykjavik/Keflavik 进入正式名单；Tromso 和 Lapland 作为北极/冬季旅游例外纳入。
- 旅游例外口径：Corsica、Salzburg/Innsbruck、Tromso、Lapland 不是按传统城市体量进入，而是用于承接季节峰值、天气扰动、包机/低成本航线、机场商业波动和区域供给弹性测试。

## 北美城市机场市场

北美区域正式纳入 40 个城市/都市圈机场市场。本轮覆盖美国和加拿大；墨西哥已归入拉美/加勒比区域。这个区域按“超大国内航空市场 + 航司枢纽 + 多机场城市群 + 长距离国内线 + 旅游/会展例外 + 加拿大八大机场”筛选，适合测试航司 hub、低成本外溢、转机银行、容量瓶颈、天气扰动和跨境需求变化。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `new_york_airport_system` | 纽约 | JFK + Newark + LaGuardia | 美国最大多机场系统之一，国际门户、商务、拥堵和航班延误压力都强 |
| `los_angeles_airport_system` | 洛杉矶 | LAX + Burbank + Long Beach + Ontario + Orange County | 南加州多机场系统，长途、娱乐产业、低成本外溢和地面交通约束并存 |
| `chicago_airport_system` | 芝加哥 | O'Hare + Midway | 美国中部超级枢纽，O'Hare 长途/联程与 Midway 低成本分工明显 |
| `dallas_fort_worth_airport_system` | 达拉斯-沃斯堡 | DFW + Love Field | American Airlines 巨型枢纽 + Southwest 城市机场，双机场分工清晰 |
| `atlanta_airport_system` | 亚特兰大 | Hartsfield-Jackson 单核心 | Delta 超级枢纽，全球最繁忙机场之一，转机和东南部腹地极强 |
| `denver_airport_system` | 丹佛 | Denver 单核心 | 美国中西部大型枢纽，国内联程、低成本增长和天气扰动都明显 |
| `san_francisco_bay_airport_system` | 旧金山湾区 | SFO + Oakland + San Jose | 湾区多机场系统，科技商务、亚洲长途和低成本外溢并存 |
| `seattle_airport_system` | 西雅图 | Sea-Tac 单核心 | 太平洋西北门户，科技商务、阿拉斯加/亚洲连接和容量压力明显 |
| `miami_south_florida_airport_system` | 迈阿密/南佛罗里达 | Miami + Fort Lauderdale + Palm Beach | 拉美门户、邮轮/休闲和低成本外溢，三机场分工明显 |
| `houston_airport_system` | 休斯敦 | IAH + Hobby | 能源商务、拉美连接和 Southwest 补充机场分工 |
| `washington_baltimore_airport_system` | 华盛顿-巴尔的摩 | Reagan National + Dulles + BWI | 政治商务、国际门户和低成本外溢的三机场系统 |
| `boston_airport_system` | 波士顿 | Logan 单核心 | 新英格兰门户，教育、科技、医疗和跨大西洋需求强 |
| `phoenix_airport_system` | 菲尼克斯 | Sky Harbor 单核心 | 西南部增长市场，国内干线、休闲和低成本航空需求强 |
| `charlotte_airport_system` | 夏洛特 | Charlotte Douglas 单核心 | American Airlines 东南部枢纽，转机占比高 |
| `philadelphia_airport_system` | 费城 | Philadelphia 单核心 | 东北走廊门户，商务、历史旅游和 American Airlines 网络节点 |
| `detroit_airport_system` | 底特律 | Detroit Metro 单核心 | 汽车工业和 Delta 枢纽，五大湖区域连接稳定 |
| `minneapolis_airport_system` | 明尼阿波利斯-圣保罗 | MSP 单核心 | 北部中转枢纽，Delta 网络、严寒天气和区域航空依赖明显 |
| `salt_lake_city_airport_system` | 盐湖城 | Salt Lake City 单核心 | 山地西部枢纽，Delta 网络、滑雪旅游和国内联程需求 |
| `san_diego_airport_system` | 圣迭戈 | San Diego 单核心 | 南加州城市门户，休闲、商务和机场地理约束明显 |
| `tampa_bay_airport_system` | 坦帕湾 | Tampa + St. Pete-Clearwater | 佛罗里达西岸增长市场，休闲、退休旅居和低成本补充需求 |
| `nashville_airport_system` | 纳什维尔 | Nashville 单核心 | 美国南部高增长城市，音乐旅游、商务和低成本航空增长强 |
| `austin_airport_system` | 奥斯汀 | Austin-Bergstrom 单核心 | 科技和人口增长市场，商务、会展和休闲需求上行 |
| `raleigh_durham_airport_system` | 罗利-达勒姆 | Raleigh-Durham 单核心 | 研究三角区门户，科技、教育和区域商务需求稳定 |
| `portland_airport_system` | 波特兰 | Portland 单核心 | 太平洋西北第二门户，休闲、科技和西海岸连接 |
| `san_antonio_airport_system` | 圣安东尼奥 | San Antonio 单核心 | 得州旅游/军事/区域商务市场，和奥斯汀形成近距离竞争 |
| `st_louis_airport_system` | 圣路易斯 | St. Louis Lambert 单核心 | 中西部老枢纽城市，区域商务和恢复型航空需求 |
| `indianapolis_airport_system` | 印第安纳波利斯 | Indianapolis 单核心 | 中西部州府门户，会议、商务和货运背景较强 |
| `orlando_airport_system` | 奥兰多 | Orlando + Sanford | 超大型旅游目的地例外，主题乐园、家庭休闲和廉航需求极强 |
| `las_vegas_airport_system` | 拉斯维加斯 | Harry Reid 单核心 | 超大型旅游/会展例外，博彩、会展、周末休闲和航空价格敏感度高 |
| `honolulu_hawaii_airport_system` | 檀香山/夏威夷 | Honolulu 单核心 | 岛屿旅游 + 太平洋门户，远程休闲、岛内连接和供给弹性重要 |
| `anchorage_alaska_airport_system` | 安克雷奇/阿拉斯加 | Anchorage 单核心 | 阿拉斯加门户，远程民生、货运和北太平洋航路价值强 |
| `new_orleans_airport_system` | 新奥尔良 | Louis Armstrong New Orleans 单核心 | 旅游/会展/邮轮城市，节庆波动和休闲需求明显 |
| `toronto_airport_system` | 多伦多 | Pearson + Billy Bishop | 加拿大最大都市机场系统，国际门户、商务和市区机场分工 |
| `vancouver_airport_system` | 温哥华 | Vancouver 单核心 | 加拿大西部门户，亚太连接、旅游和跨太平洋需求强 |
| `montreal_airport_system` | 蒙特利尔 | Montreal-Trudeau 单核心 | 魁北克门户，法语区商务、欧洲连接和航空制造业背景 |
| `calgary_airport_system` | 卡尔加里 | Calgary 单核心 | 加拿大西部和能源商务门户，WestJet 枢纽属性明显 |
| `edmonton_airport_system` | 埃德蒙顿 | Edmonton 单核心 | 阿尔伯塔北部门户，能源、政府和区域连接需求 |
| `ottawa_airport_system` | 渥太华 | Ottawa 单核心 | 加拿大首都门户，政府公务、商务和国内干线需求 |
| `winnipeg_airport_system` | 温尼伯 | Winnipeg 单核心 | 加拿大中部门户，区域连接、货运和北方支线价值 |
| `halifax_airport_system` | 哈利法克斯 | Halifax Stanfield 单核心 | 加拿大大西洋门户，旅游、海港经济和跨大西洋恢复需求 |

北美当前纳入 ID：

```text
new_york_airport_system
los_angeles_airport_system
chicago_airport_system
dallas_fort_worth_airport_system
atlanta_airport_system
denver_airport_system
san_francisco_bay_airport_system
seattle_airport_system
miami_south_florida_airport_system
houston_airport_system
washington_baltimore_airport_system
boston_airport_system
phoenix_airport_system
charlotte_airport_system
philadelphia_airport_system
detroit_airport_system
minneapolis_airport_system
salt_lake_city_airport_system
san_diego_airport_system
tampa_bay_airport_system
nashville_airport_system
austin_airport_system
raleigh_durham_airport_system
portland_airport_system
san_antonio_airport_system
st_louis_airport_system
indianapolis_airport_system
orlando_airport_system
las_vegas_airport_system
honolulu_hawaii_airport_system
anchorage_alaska_airport_system
new_orleans_airport_system
toronto_airport_system
vancouver_airport_system
montreal_airport_system
calgary_airport_system
edmonton_airport_system
ottawa_airport_system
winnipeg_airport_system
halifax_airport_system
```

北美名称备注：

- 美国多机场系统：纽约、洛杉矶、芝加哥、达拉斯-沃斯堡、旧金山湾区、南佛罗里达、休斯敦、华盛顿-巴尔的摩都按都市圈机场系统处理，不拆成单机场经营对象。
- 美国航司枢纽：亚特兰大、达拉斯-沃斯堡、芝加哥、丹佛、夏洛特、明尼阿波利斯、盐湖城、底特律、休斯敦等适合测试航司 hub 与转机银行。
- 美国增长城市：纳什维尔、奥斯汀、罗利-达勒姆、坦帕湾、圣迭戈、菲尼克斯等用于表达美国人口迁移、低成本航空和 Sun Belt 增长。
- 旅游/特殊例外：奥兰多、拉斯维加斯、檀香山/夏威夷、安克雷奇/阿拉斯加、新奥尔良进入正式名单，用于承接主题乐园、博彩会展、岛屿远程旅游、远程民生/货运和节庆型需求。
- 加拿大：多伦多、温哥华、蒙特利尔、卡尔加里、埃德蒙顿、渥太华、温尼伯、哈利法克斯覆盖加拿大主要机场经营对象；Quebec City、Victoria、Kelowna、Saskatoon、Regina、St. John's 先放观察池。
- 暂不纳入：Memphis、Louisville 以后如果做货运层可以单独补强；Kansas City、Cleveland、Pittsburgh、Columbus、Milwaukee、Cincinnati、Sacramento 先放观察池。

## 拉美/加勒比城市机场市场

拉美/加勒比区域正式纳入 40 个城市/都市圈机场市场。这个区域按“首都/国家门户 + 大型航司枢纽 + 巴西/墨西哥/哥伦比亚主干城市 + 少数超大型旅游目的地例外”筛选，适合测试新兴市场增长、汇率和经济波动、旅游目的地冲击、机场新容量投放、跨洲联程和国内航空集中度。

| city_airport_market_id | 城市机场市场 | 当前机场格局 | 规划/潜在供给 |
|---|---|---|---|
| `mexico_city_airport_system` | 墨西哥城 | Benito Juarez + Felipe Angeles + Toluca | 墨西哥最大城市机场系统，老机场拥堵、新机场分流和航司迁移压力并存 |
| `cancun_riviera_maya_airport_system` | 坎昆/玛雅海岸 | Cancun + Tulum | 超大型旅游目的地例外，海滨度假、北美客源和新机场投放价值强 |
| `guadalajara_airport_system` | 瓜达拉哈拉 | Guadalajara 单核心 | 墨西哥西部经济门户，制造业、侨民/VFR 和北美连接需求 |
| `monterrey_airport_system` | 蒙特雷 | Monterrey 单核心 | 墨西哥北部工业和商务门户，近美供应链和货运背景明显 |
| `tijuana_airport_system` | 蒂华纳 | Tijuana 单核心 | 美墨边境机场，跨境客流、低成本国内线和 CBX 通道特征强 |
| `los_cabos_airport_system` | 洛斯卡沃斯 | Los Cabos 单核心 | 高端海滨旅游例外，美国/加拿大客源、度假酒店和季节性明显 |
| `puerto_vallarta_airport_system` | 巴亚尔塔港/纳亚里特海岸 | Puerto Vallarta 单核心 | 太平洋海岸旅游例外，休闲、退休旅居和北美航线强 |
| `merida_yucatan_airport_system` | 梅里达/尤卡坦 | Merida 单核心 | 尤卡坦门户，区域旅游、生活方式迁入和东南墨西哥增长 |
| `panama_city_airport_system` | 巴拿马城 | Tocumen + Albrook | 中美洲航空枢纽，Copa 联程网络、南北美连接和中转商业价值强 |
| `san_jose_costa_rica_airport_system` | 圣何塞/哥斯达黎加 | Juan Santamaria 单核心 | 哥斯达黎加国家门户，生态旅游、商务和北美连接需求 |
| `liberia_costa_rica_airport_system` | 利比里亚/瓜纳卡斯特 | Guanacaste 单核心 | 哥斯达黎加太平洋海岸旅游例外，度假型国际客流明显 |
| `san_salvador_airport_system` | 圣萨尔瓦多 | El Salvador International 单核心 | 中美洲门户和 Avianca 网络节点，侨民/VFR 与北美连接强 |
| `guatemala_city_airport_system` | 危地马拉城 | La Aurora 单核心 | 危地马拉国家门户，商务、探亲和中美洲区域连接 |
| `punta_cana_airport_system` | 蓬塔卡纳 | Punta Cana 单核心 | 加勒比超大型旅游目的地例外，度假酒店、包机和机场商业价值强 |
| `santo_domingo_airport_system` | 圣多明各 | Las Americas 单核心 | 多米尼加首都门户，侨民/VFR、商务和加勒比连接 |
| `san_juan_puerto_rico_airport_system` | 圣胡安/波多黎各 | Luis Munoz Marin 单核心 | 加勒比门户，北美连接、邮轮旅游和美国属地客流特征 |
| `jamaica_airport_system` | 牙买加 | Montego Bay + Kingston | 岛屿双机场系统，Montego Bay 旅游 + Kingston 首都/商务分工 |
| `nassau_bahamas_airport_system` | 拿骚/巴哈马 | Lynden Pindling 单核心 | 巴哈马门户，邮轮、海岛度假和美国短途休闲需求 |
| `sao_paulo_airport_system` | 圣保罗 | Guarulhos + Congonhas + Viracopos | 拉美最大都市机场系统之一，国际门户、国内商务和货运分工明显 |
| `rio_de_janeiro_airport_system` | 里约热内卢 | Galeao + Santos Dumont | 巴西旅游/商务双机场系统，国际门户恢复和市区机场分工 |
| `brasilia_airport_system` | 巴西利亚 | Brasilia 单核心 | 巴西首都和国内联程枢纽，政治公务和全国网络连接强 |
| `belo_horizonte_airport_system` | 贝洛奥里藏特 | Confins + Pampulha | 米纳斯吉拉斯门户，工业、区域商务和双机场补充 |
| `recife_airport_system` | 累西腓 | Recife 单核心 | 巴西东北部门户，国内干线、旅游和区域连接价值 |
| `salvador_bahia_airport_system` | 萨尔瓦多/巴伊亚 | Salvador 单核心 | 巴西东北旅游与文化门户，休闲和区域商务混合 |
| `fortaleza_airport_system` | 福塔莱萨 | Fortaleza 单核心 | 巴西东北海岸门户，旅游、欧洲连接和国内增长 |
| `porto_alegre_airport_system` | 阿雷格里港 | Porto Alegre 单核心 | 巴西南部门户，工业、农业腹地和区域恢复需求 |
| `bogota_airport_system` | 波哥大 | El Dorado 单核心 | 安第斯超级枢纽，Avianca 网络、货运和高海拔运营特征明显 |
| `medellin_airport_system` | 麦德林 | Jose Maria Cordova + Olaya Herrera | 哥伦比亚第二城市机场系统，商务、旅游和山地机场分工 |
| `cartagena_airport_system` | 卡塔赫纳 | Rafael Nunez 单核心 | 加勒比历史旅游城市，邮轮、休闲和国际增长明显 |
| `cali_airport_system` | 卡利 | Alfonso Bonilla Aragon 单核心 | 哥伦比亚西南门户，区域商务、侨民和国内干线需求 |
| `lima_airport_system` | 利马 | Jorge Chavez 单核心 | 秘鲁国家门户，新航站楼/跑道投放和南美中转价值强 |
| `cusco_airport_system` | 库斯科 | Alejandro Velasco Astete 单核心 | 世界级旅游目的地例外，马丘比丘门户和高原/容量约束明显 |
| `santiago_chile_airport_system` | 圣地亚哥/智利 | Arturo Merino Benitez 单核心 | 智利国家门户，长距离国内线、矿业商务和南太平洋连接 |
| `buenos_aires_airport_system` | 布宜诺斯艾利斯 | Ezeiza + Aeroparque | 阿根廷首都双机场系统，国际门户和市区国内/区域航线分工 |
| `cordoba_argentina_airport_system` | 科尔多瓦/阿根廷 | Cordoba 单核心 | 阿根廷内陆第二层级门户，国内连接和区域经济腹地 |
| `mendoza_airport_system` | 门多萨 | Mendoza 单核心 | 葡萄酒旅游、安第斯门户和智利/阿根廷区域连接 |
| `quito_airport_system` | 基多 | Mariscal Sucre 单核心 | 厄瓜多尔首都门户，高海拔、商务和安第斯区域连接 |
| `guayaquil_airport_system` | 瓜亚基尔 | Jose Joaquin de Olmedo 单核心 | 厄瓜多尔最大港口城市门户，商务、侨民和海岸旅游 |
| `montevideo_airport_system` | 蒙得维的亚 | Carrasco 单核心 | 乌拉圭国家门户，商务、休闲和布宜诺斯艾利斯外溢 |
| `santa_cruz_bolivia_airport_system` | 圣克鲁斯/玻利维亚 | Viru Viru 单核心 | 玻利维亚低地经济门户，国内联程、区域商务和国际连接价值 |

拉美/加勒比当前纳入 ID：

```text
mexico_city_airport_system
cancun_riviera_maya_airport_system
guadalajara_airport_system
monterrey_airport_system
tijuana_airport_system
los_cabos_airport_system
puerto_vallarta_airport_system
merida_yucatan_airport_system
panama_city_airport_system
san_jose_costa_rica_airport_system
liberia_costa_rica_airport_system
san_salvador_airport_system
guatemala_city_airport_system
punta_cana_airport_system
santo_domingo_airport_system
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
