// 分局按连接边界划分，归属随站点连接网络计算；不切断实际铁路。
window.RAILWAY_DIVISIONS = [
  {
    id: 'jiamusi', name: '佳木斯铁路分局公司', seedStationId: 'hamujia_06',
    boundaryEdgeIds: [
      'high_speed:hamujia_03|hamujia_04',
      'high_speed:ha_jm_demoli|ha_jm_fangzheng',
      'conventional:ha_yc_tieli|suihua_jiamusi_taoshan'
    ]
  },
  {
    id: 'mudanjiang', name: '牡丹江铁路分局公司', seedStationId: 'hamujia_02',
    boundaryEdgeIds: [
      'high_speed:hamu_hengdaohezi_dong|hamu_yabulixi',
      'high_speed:hamujia_03|hamujia_04',
      'conventional:mudanjiang_tumen_dongjingcheng|mudanjiang_tumen_ludao'
    ]
  },
  {
    id: 'qiqihar', name: '齐齐哈尔铁路分局公司', seedStationId: 'binzhou_03',
    boundaryEdgeIds: [
      'high_speed:haqi_anda|haqi_daqingdong',
      'conventional:siping_qiqihar_tailai|siping_qiqihar_zhenlai',
      'conventional:tongliao_daqing_daanbei|tongliao_daqing_xinzhao',
      'conventional:harbin_heihe_beian|qiqi_beian_kedong'
    ]
  },
  {
    id: 'harbin', name: '哈尔滨铁路分局公司', seedStationId: 'harbin',
    boundaryEdgeIds: [
      'high_speed:hada_fuyubei|hada_shuangchengbei',
      'high_speed:haqi_anda|haqi_daqingdong',
      'high_speed:hamu_hengdaohezi_dong|hamu_yabulixi',
      'high_speed:ha_jm_demoli|ha_jm_fangzheng',
      'conventional:ha_yc_tieli|suihua_jiamusi_taoshan',
      'conventional:harbin_heihe_beian|qiqi_beian_kedong'
    ]
  },
  {
    id: 'meihekou', name: '梅河口铁路分局公司', seedStationId: 'shenyangjilin_meihekou',
    boundaryEdgeIds: [
      'conventional:changtongbai_02|siping_meihekou_shiling',
      'conventional:shenyangjilin_caoshi|shenyangjilin_shanchengzhen',
      'conventional:shenyangjilin_chaoyangzhen|shenyangjilin_panshi',
      'high_speed:shenbai_tonghua|shenbai_xinbin',
      'high_speed:shenbai_changbaishan|shenbai_changbaishanxi'
    ]
  },
  {
    id: 'changchun', name: '长春铁路分局公司', seedStationId: 'changchun',
    boundaryEdgeIds: [
      'high_speed:hada_fuyubei|hada_shuangchengbei',
      'high_speed:hada_gongzhulingnan|jingha_07',
      'conventional:shenyangjilin_chaoyangzhen|shenyangjilin_panshi',
      'high_speed:shenbai_changbaishan|shenbai_changbaishanxi',
      'conventional:siping_qiqihar_tailai|siping_qiqihar_zhenlai',
      'conventional:tongliao_daqing_daanbei|tongliao_daqing_xinzhao',
      'conventional:tongliao_daqing_baolongshan|tongliao_daqing_taipingchuan',
      'conventional:siping_qiqihar_baokang|siping_qiqihar_maolin'
    ]
  },
  {
    id: 'siping', name: '四平铁路分局公司', seedStationIds: ['siping', 'jingha_07'],
    boundaryEdgeIds: [
      'high_speed:hada_gongzhulingnan|jingha_07',
      'high_speed:hada_changtuxi|jingha_07',
      'conventional:changtongbai_02|siping_meihekou_shiling',
      'conventional:siping_qiqihar_baokang|siping_qiqihar_maolin',
      'conventional:dahushan_ouli|dahushan_shuangliao'
    ]
  },
  {
    id: 'tongliao', name: '通辽铁路分局公司', seedStationId: 'jingha_chifeng_03',
    boundaryEdgeIds: [
      'conventional:tongliao_daqing_baolongshan|tongliao_daqing_taipingchuan',
      'conventional:dahushan_ouli|dahushan_shuangliao',
      'conventional:jingha_ganqika|jingha_zhangwu',
      'high_speed:jingha_ganqika|jingha_zhanggutai',
      'conventional:daban|kailu',
      'conventional:jingtong_aohan|jingtong_naiman'
    ]
  },
  {
    id: 'shenyang', name: '沈阳铁路分局公司', seedStationId: 'jingha_shenyang',
    boundaryEdgeIds: [
      'high_speed:hada_changtuxi|jingha_07',
      'conventional:shenyangjilin_caoshi|shenyangjilin_shanchengzhen',
      'high_speed:shenbai_tonghua|shenbai_xinbin',
      'high_speed:jingha_ganqika|jingha_zhanggutai',
      'conventional:jingha_ganqika|jingha_zhangwu',
      'high_speed:jingha_heishanbei|jingha_xinminbei',
      'high_speed:jingha_panjinbei|jingha_taian',
      'conventional:jingha_zhangwu|jinzhou_xinlitun_xinlitun',
      'high_speed:hada_haichengxi|shenda_branch_02',
      'high_speed:hada_haichengxi|shenda_04',
      'high_speed:danda_01|danda_dandongxi'
    ]
  },
  {
    id: 'dalian', name: '大连铁路分局公司', seedStationId: 'shenda_05',
    boundaryEdgeIds: [
      'high_speed:hada_haichengxi|shenda_04',
      'high_speed:shenda_04|shenda_branch_02',
      'high_speed:danda_01|danda_dandongxi',
      'conventional:yanda_lushunxi|yanda_yantaibei'
    ]
  },
  {
    id: 'jinzhou', name: '锦州铁路分局公司', seedStationIds: ['jinzhou', 'jinqinshen_05'],
    boundaryEdgeIds: [
      'high_speed:jingha_heishanbei|jingha_xinminbei',
      'high_speed:jingha_panjinbei|jingha_taian',
      'high_speed:hada_haichengxi|shenda_branch_02',
      'conventional:jingha_zhangwu|jinzhou_xinlitun_xinlitun',
      'high_speed:shenda_04|shenda_branch_02',
      'high_speed:qinshen_dongdaihe|qinshen_shanhaiguan',
      'high_speed:jingha_niuheliang|jingha_pingquanbei',
      'conventional:jinzhou_chengde_pingquan|jinzhou_chengde_sanshijia',
      'high_speed:jingha_jianping|jingha_ningcheng',
      'conventional:jingtong_tianyi|jinzhou_chengde_yebaishou'
    ]
  },
  {
    id: 'chifeng', name: '赤峰铁路分局公司', seedStationIds: ['jingha_chifeng_02', 'jingtong_chifengnan'],
    boundaryEdgeIds: [
      'high_speed:jingha_jianping|jingha_ningcheng',
      'conventional:jingtong_tianyi|jinzhou_chengde_yebaishou',
      'conventional:jingtong_aohan|jingtong_naiman',
      'conventional:daban|kailu',
      'conventional:jingtong_chaoyangdi|jingtong_siheyong',
      'conventional:jingpeng|sanggendalai'
    ]
  },
  {
    id: 'zhangjiakou', name: '张家口铁路分局公司', seedStationIds: ['jingbao_02', 'zhangtang_zhangjiakounan'],
    boundaryEdgeIds: [
      'high_speed:jingbao_badaling|jingbao_donghuayuanbei',
      'conventional:zhangtang_chicheng|zhangtang_fengning',
      'high_speed:jingbao_huaian|zhanghu_xinghebei',
      'high_speed:jingbao_huaian|zhangdaxi_tianzhen',
      'high_speed:dabao_laiyuan|shizhang_xiheying',
      'conventional:huade|zhengxiangbaiqi',
      'conventional:jingpeng|sanggendalai'
    ]
  },
  {
    id: 'beijing', name: '北京铁路分局公司', seedStationIds: ['jingguang_01', 'jingbao_01', 'jingtang_01'],
    boundaryEdgeIds: [
      'high_speed:jingbao_badaling|jingbao_donghuayuanbei',
      'conventional:zhangtang_chicheng|zhangtang_fengning',
      'high_speed:jingha_niuheliang|jingha_pingquanbei',
      'conventional:jinzhou_chengde_pingquan|jinzhou_chengde_sanshijia',
      'conventional:jingtong_chaoyangdi|jingtong_siheyong',
      'conventional:zhangtang_fengrunxi|zhangtang_tuanpiaozhuang',
      'high_speed:jingjin_yizhuang|wuqing',
      'high_speed:langfang|jinxing_01',
      'high_speed:jingtang_04|jingtang_05',
      'high_speed:jinxing_02|jinxing_shengfang',
      'high_speed:jingxiong_04|jingxiong_05',
      'high_speed:jingxiongshang_02|jingxiongshang_shuangxin',
      'high_speed:jingguang_02|jingguang_gaobeidiandong'
    ]
  },
  {
    id: 'tangshan', name: '唐山铁路分局公司', seedStationId: 'jinqinshen_02',
    boundaryEdgeIds: [
      'high_speed:jingtang_04|jingtang_05',
      'high_speed:jingbin_binhaibei|jinqinshen_02',
      'conventional:zhangtang_fengrunxi|zhangtang_tuanpiaozhuang',
      'high_speed:qinshen_dongdaihe|qinshen_shanhaiguan'
    ]
  },
  {
    id: 'tianjin', name: '天津铁路分局公司', seedStationId: 'tianjin',
    boundaryEdgeIds: [
      'high_speed:jingjin_yizhuang|wuqing',
      'high_speed:langfang|jinxing_01',
      'high_speed:jinxing_02|jinxing_shengfang',
      'high_speed:jingbin_binhaibei|jinqinshen_02',
      'high_speed:tuanpobei|wenanbei',
      'high_speed:hengcang_fuchengnan|shihuang_jiaohe',
      'high_speed:jinghu_04|jinghu_05',
      'high_speed:jinwei_haixingxi|jinwei_wudi'
    ]
  },
  {
    id: 'xiongan', name: '雄安铁路分局公司', seedStationId: 'jingxiongshang_02',
    boundaryEdgeIds: [
      'high_speed:jingxiong_04|jingxiong_05',
      'high_speed:jingxiongshang_02|jingxiongshang_shuangxin',
      'high_speed:jingguang_02|jingguang_gaobeidiandong',
      'high_speed:tuanpobei|wenanbei',
      'high_speed:jingguang_dingzhoudong|jingguang_zhengdingairport',
      'high_speed:shibao_anguodong|shibao_wuji',
      'high_speed:jinxiongxin_quyang|shizhang_xingtang',
      'high_speed:jingxiongshang_shenzhoudong|jingxiongshang_suninghejian',
      'high_speed:dabao_laiyuan|shizhang_xiheying',
      'high_speed:dabao_laiyuan|dabao_lingqiu',
      'high_speed:jinxiongxin_fuping|jinxiongxin_wutaishan'
    ]
  },
  {
    id: 'shijiazhuang', name: '石家庄铁路分局公司', seedStationId: 'jingguang_03',
    boundaryEdgeIds: [
      'high_speed:jingguang_dingzhoudong|jingguang_zhengdingairport',
      'high_speed:shibao_anguodong|shibao_wuji',
      'high_speed:jinxiongxin_quyang|shizhang_xingtang',
      'high_speed:jingxiongshang_shenzhoudong|jingxiongshang_suninghejian',
      'high_speed:hengcang_fuchengnan|shihuang_jiaohe',
      'high_speed:shita_02|shita_jingxingbei',
      'high_speed:jinghu_05|shiji_jingzhou',
      'high_speed:jingxiongshang_linqingdong|jingxiongshang_qinghexi',
      'high_speed:jingguang_05|jingguang_06',
      'high_speed:liaohanchang_lichengnan|liaohanchang_shexiannan',
      'high_speed:liaohanchang_guantaonan|liaohanchang_guanxiannan'
    ]
  },
  {
    id: 'datong', name: '大同铁路分局公司', seedStationId: 'zhangdaxi_02',
    boundaryEdgeIds: [
      'high_speed:jingbao_huaian|zhangdaxi_tianzhen',
      'high_speed:dabao_laiyuan|dabao_lingqiu',
      'high_speed:zhangdaxi_03|zhangdaxi_yanmenguan',
      'high_speed:jida_fengzhenbei|jingbao_03',
      'high_speed:hushuo_helingeer|hushuo_youyu'
    ]
  },
  {
    id: 'taiyuan', name: '太原铁路分局公司', seedStationId: 'zhangdaxi_05',
    boundaryEdgeIds: [
      'high_speed:zhangdaxi_03|zhangdaxi_yanmenguan',
      'high_speed:jinxiongxin_fuping|jinxiongxin_wutaishan',
      'high_speed:shita_02|shita_jingxingbei',
      'high_speed:zhengtai_wuxiang|zhengtai_yushexi',
      'high_speed:zhangdaxi_huozhoudong|zhangdaxi_lingshidong',
      'high_speed:taisui_liulinxi|yanyu_suidexi'
    ]
  },
  {
    id: 'changzhi', name: '长治铁路分局公司', seedStationIds: ['zhengtai_04', 'houyue_qinshui'],
    boundaryEdgeIds: [
      'high_speed:zhengtai_wuxiang|zhengtai_yushexi',
      'high_speed:liaohanchang_lichengnan|liaohanchang_shexiannan',
      'high_speed:linchang_anze|linchang_fushan',
      'high_speed:zhengtai_03|zhengtai_jiaozuoxi',
      'conventional:houyue_qinshui|houyue_yicheng',
      'conventional:houyue_jiyuan|houyue_yangcheng'
    ]
  },
  {
    id: 'houma', name: '侯马铁路分局公司', seedStationId: 'houma_houma',
    boundaryEdgeIds: [
      'high_speed:zhangdaxi_huozhoudong|zhangdaxi_lingshidong',
      'high_speed:linchang_anze|linchang_fushan',
      'conventional:houyue_qinshui|houyue_yicheng',
      'high_speed:zhangdaxi_dali|zhangdaxi_yongjibei',
      'high_speed:xihanhou_hejin|yunhan_hanchengdong',
      'high_speed:lianxulan_07|zhangdaxi_08'
    ]
  },
  {
    id: 'jining', name: '集宁铁路分局公司', seedStationId: 'jiningnan',
    boundaryEdgeIds: [
      'high_speed:jingbao_huaian|zhanghu_xinghebei',
      'high_speed:jida_fengzhenbei|jingbao_03',
      'high_speed:jingbao_qixianyingnan|jingbao_zhuozidong',
      'conventional:huade|zhengxiangbaiqi'
    ]
  },
  {
    id: 'hohhot', name: '呼和浩特铁路分局公司', seedStationId: 'jingbao_04',
    boundaryEdgeIds: [
      'high_speed:jingbao_qixianyingnan|jingbao_zhuozidong',
      'high_speed:jingbao_chasuqi|jingbao_salaqi',
      'high_speed:hushuo_helingeer|hushuo_youyu',
      'high_speed:baohu_dongshengdong|dae_zhungeer'
    ]
  },
  {
    id: 'baotou', name: '包头铁路分局公司', seedStationId: 'jingbao_05',
    boundaryEdgeIds: [
      'high_speed:jingbao_chasuqi|jingbao_salaqi',
      'high_speed:baohu_dongshengdong|dae_zhungeer',
      'high_speed:xiyubao_04|xiyubao_05',
      'high_speed:baoyin_huinongnan|baoyin_wuhainan',
      'conventional:linha_ejina|linha_mazongshan'
    ]
  },
  {
    id: 'yinchuan', name: '银川铁路分局公司', seedStationId: 'baoyin_06',
    boundaryEdgeIds: [
      'high_speed:baoyin_huinongnan|baoyin_wuhainan',
      'high_speed:xiyin_04|yinlan_hongsibaobei',
      'conventional:taiyin_yanchi|yanzhong_hongsibao',
      'high_speed:taiyin_dingbian|taiyin_yanchi',
      'high_speed:xiyin_huanxian|xiyin_tianshuibu'
    ]
  },
  {
    id: 'zhongwei', name: '中卫铁路分局公司', seedStationId: 'baozhong_zhongwei',
    boundaryEdgeIds: [
      'high_speed:xiyin_04|yinlan_hongsibaobei',
      'conventional:taiyin_yanchi|yanzhong_hongsibao',
      'high_speed:yinlan_03|yinlan_beitan',
      'conventional:ganwu_gantang|ganwu_tanjiajing',
      'conventional:baozhong_02|baozhong_03'
    ]
  },
  {
    id: 'xian', name: '西安铁路分局公司', seedStationId: 'xiping_xian',
    boundaryEdgeIds: [
      'high_speed:lianxulan_qishan|lianxulan_yanglingnan',
      'high_speed:xiyu_02|xiyu_zhenanxi',
      'high_speed:xicheng_foping|xicheng_yangxianxi',
      'high_speed:yanyu_qingjianbei|yanyu_yanchuan',
      'high_speed:zhangdaxi_dali|zhangdaxi_yongjibei',
      'high_speed:xihanhou_hejin|yunhan_hanchengdong',
      'high_speed:lianxulan_huashanbei|lianxulan_lingbaoxi',
      'high_speed:shangnan_shangnandong|shangnan_xixiadong',
      'high_speed:xiwu_manchuanguan|xiwu_yunxi',
      'high_speed:xiyin_binzhoudong|xiyin_ningxian',
      'conventional:xiping_changqingqiao|xiping_changwu'
    ]
  },
  {
    id: 'baoji', name: '宝鸡铁路分局公司', seedStationId: 'baoji_baoji',
    boundaryEdgeIds: [
      'high_speed:lianxulan_qishan|lianxulan_yanglingnan',
      'high_speed:lianxulan_11|lianxulan_dongcha',
      'conventional:baozhong_ankouyao|baozhong_longxian',
      'conventional:baocheng_yangpingguan|baocheng_yanzibian'
    ]
  },
  {
    id: 'ankang', name: '安康铁路分局公司', seedStationId: 'xiyu_02',
    boundaryEdgeIds: [
      'high_speed:xiyu_02|xiyu_zhenanxi',
      'high_speed:xicheng_foping|xicheng_yangxianxi',
      'high_speed:hananshi_baihe|xiwu_03',
      'high_speed:xicheng_chaotiannan|xicheng_ningqiangnan',
      'high_speed:xiyu_chengkou|xiyu_langao',
      'high_speed:chengbaan_wanyuanbei|chengbaan_ziyangnan'
    ]
  },
  {
    id: 'suidexi', name: '绥德铁路分局公司', seedStationId: 'yanyu_suidexi',
    boundaryEdgeIds: [
      'high_speed:xiyubao_04|xiyubao_05',
      'high_speed:taisui_liulinxi|yanyu_suidexi',
      'high_speed:taiyin_dingbian|taiyin_yanchi',
      'high_speed:yanyu_qingjianbei|yanyu_yanchuan'
    ]
  },
  {
    id: 'lanzhou', name: '兰州铁路分局公司', seedStationId: 'langyu_lanzhou',
    boundaryEdgeIds: [
      'high_speed:lianxulan_11|lianxulan_dongcha',
      'conventional:dingping_huining|dingping_jingning',
      'conventional:baozhong_huating|tianping_zhangjiachuan',
      'high_speed:lanzhang_tianzhuxi|lanzhang_yongdengbei',
      'high_speed:yinlan_03|yinlan_beitan',
      'high_speed:lanxin_haidong|lanxin_minhenan',
      'conventional:chuanqing_04|chuanqing_ganjia',
      'conventional:langyu_02|langyu_yaodu',
      'conventional:chuanqing_huahu|chuanqing_langmusi'
    ]
  },
  {
    id: 'pingliang', name: '平凉铁路分局公司', seedStationId: 'baozhong_02',
    boundaryEdgeIds: [
      'conventional:dingping_huining|dingping_jingning',
      'conventional:baozhong_huating|tianping_zhangjiachuan',
      'conventional:baozhong_02|baozhong_03',
      'conventional:baozhong_ankouyao|baozhong_longxian',
      'conventional:xiping_changqingqiao|xiping_changwu',
      'high_speed:xiyin_binzhoudong|xiyin_ningxian',
      'high_speed:xiyin_huanxian|xiyin_tianshuibu'
    ]
  },
  {
    id: 'wuwei', name: '武威铁路分局公司', seedStationIds: ['lanzhang_02','ganwu_wuweinan'],
    boundaryEdgeIds: [
      'high_speed:lanzhang_tianzhuxi|lanzhang_yongdengbei',
      'high_speed:lanzhang_03|lanzhang_jilingxi',
      'conventional:ganwu_gantang|ganwu_tanjiajing'
    ]
  },
  {
    id: 'zhangye', name: '张掖铁路分局公司', seedStationIds: ['lanxin_04','linha_mazongshan'],
    boundaryEdgeIds: [
      'high_speed:lanzhang_03|lanzhang_jilingxi',
      'high_speed:lanxin_menyuan|lanxin_shandanmachang',
      'high_speed:lanxin_07|lanxin_liuyuannan',
      'conventional:dunge_dangjinshan|dunge_suganhu',
      'conventional:linha_ejina|linha_mazongshan',
      'conventional:linha_mingshui|linha_wutongshui'
    ]
  },
  {
    id: 'xining', name: '西宁铁路分局公司', seedStationId: 'lanxin_03',
    boundaryEdgeIds: [
      'high_speed:lanxin_haidong|lanxin_minhenan',
      'high_speed:lanxin_menyuan|lanxin_shandanmachang',
      'conventional:chuanqing_04|chuanqing_ganjia',
      'conventional:qingzang_gangcha|qingzang_tianjun'
    ]
  },
  {
    id: 'golmud', name: '格尔木铁路分局公司', seedStationId: 'qingzang_03',
    boundaryEdgeIds: [
      'conventional:qingzang_gangcha|qingzang_tianjun',
      'conventional:dunge_dangjinshan|dunge_suganhu',
      'conventional:geku_milan|geku_yitunbulake',
      'conventional:qingzang_anduo|qingzang_tanggula'
    ]
  },
  {
    id: 'hami', name: '哈密铁路分局公司', seedStationId: 'lanxin_07',
    boundaryEdgeIds: [
      'high_speed:lanxin_07|lanxin_liuyuannan',
      'conventional:linha_mingshui|linha_wutongshui',
      'high_speed:lanxin_shanshanbei|lanxin_tuha',
      'conventional:geku_milandong|hamimi_luozhong'
    ]
  },
  {
    id: 'urumqi', name: '乌鲁木齐铁路分局公司', seedStationIds: ['lanxin_09','nanjiang_tuokexun'],
    boundaryEdgeIds: [
      'high_speed:lanxin_shanshanbei|lanxin_tuha',
      'conventional:beijiang_shawanshi|beijiang_shihezi',
      'conventional:afuzhun_fuyun|beijiang_03',
      'conventional:nanjiang_malan|nanjiang_tuokexun'
    ]
  },
  {
    id: 'kuitun', name: '奎屯铁路分局公司', seedStationId: 'beijiang_01',
    boundaryEdgeIds: [
      'conventional:beijiang_shawanshi|beijiang_shihezi',
      'conventional:afuzhun_fuyun|beijiang_03',
      'conventional:kue_kutaikelike|yia_bayinbuluke'
    ]
  },
  {
    id: 'korla', name: '库尔勒铁路分局公司', seedStationId: 'nanjiang_01',
    boundaryEdgeIds: [
      'conventional:geku_milandong|hamimi_luozhong',
      'conventional:kue_kutaikelike|yia_bayinbuluke',
      'conventional:geku_milan|geku_yitunbulake',
      'conventional:nanjiang_03|nanjiang_bachu',
      'conventional:heruo_02|heruo_minfeng',
      'conventional:nanjiang_malan|nanjiang_tuokexun'
    ]
  },
  {
    id: 'kashgar', name: '喀什铁路分局公司', seedStationId: 'nanjiang_04',
    boundaryEdgeIds: [
      'conventional:nanjiang_03|nanjiang_bachu',
      'conventional:heruo_02|heruo_minfeng'
    ]
  },
  {
    id: 'lhasa', name: '拉萨铁路分局公司', seedStationId: 'chuanzang_07',
    boundaryEdgeIds: [
      'conventional:qingzang_anduo|qingzang_tanggula',
      'conventional:chuanzang_baiyu|chuanzang_gongjue',
      'conventional:dianzang_deqin|dianzang_yanjing'
    ]
  },
  {
    id: 'chengdu', name: '成都铁路分局公司', seedStationIds: ['xicheng_06','yixipan_leibo'],
    boundaryEdgeIds: [
      'high_speed:chengdawan_03|chengdawan_tongnan',
      'high_speed:chengyu_anyue|chengyu_dazushike',
      'high_speed:chengyu_longchangbei|chengyu_rongchangbei',
      'high_speed:xicheng_jiangyoubei|xicheng_qingchuan',
      'high_speed:chengbaan_yanting|miansuinei_santai',
      'high_speed:chengdawan_pengxinan|langyu_04',
      'high_speed:chengyi_weiyuan|chengyi_zizhongxi',
      'high_speed:chengyu_03|chengziyi_03',
      'high_speed:chenggui_nixi|chenggui_qianwei',
      'conventional:yixipan_leibo|yixipan_suijiang',
      'conventional:chengkun_03|chengkun_yongren',
      'conventional:chuanzang_baiyu|chuanzang_gongjue',
      'conventional:chuanqing_huahu|chuanqing_langmusi'
    ]
  },
  {
    id: 'chongqing', name: '重庆铁路分局公司', seedStationId: 'huyurong_14',
    boundaryEdgeIds: [
      'high_speed:langyu_04|langyu_wusheng',
      'high_speed:xiyu_dazu|xiyu_guangandong',
      'high_speed:yuwan_dianjiang|yuwan_liangpingnan',
      'high_speed:yuwan_fengdubei|yuwan_zhongxian',
      'high_speed:wanqian_shizhu|yuxia_pengshuixi',
      'high_speed:yifu_huangshui|yifu_lichuan',
      'high_speed:yuxia_02|yuxia_xianfeng',
      'conventional:yuhuai_tongren|yuhuai_xiushan',
      'high_speed:yugui_qijiangdong|yugui_tongzidong',
      'high_speed:yugui2_wansheng|yugui2_zhengan',
      'high_speed:yukun_baisha|yukun_hejiang',
      'high_speed:yukun_luzhoudong|yukun_yongchuannan',
      'high_speed:chengdawan_03|chengdawan_tongnan',
      'high_speed:chengyu_anyue|chengyu_dazushike',
      'high_speed:chengyu_longchangbei|chengyu_rongchangbei'
    ]
  },
  {
    id: 'guangyuan', name: '广元铁路分局公司', seedStationIds: ['xicheng_03','chengbaan_yanting'],
    boundaryEdgeIds: [
      'high_speed:xicheng_jiangyoubei|xicheng_qingchuan',
      'high_speed:chengbaan_yanting|miansuinei_santai',
      'high_speed:chengdawan_pengxinan|langyu_04',
      'high_speed:bazhong_01|guangbada_pingchang',
      'high_speed:chengbaan_bazhongdong|chengbaan_tongjiang',
      'high_speed:chengdawan_quxianbei|chengdawan_yingshanxi',
      'high_speed:langyu_04|langyu_wusheng',
      'high_speed:xicheng_chaotiannan|xicheng_ningqiangnan',
      'conventional:baocheng_yangpingguan|baocheng_yanzibian',
      'conventional:langyu_02|langyu_yaodu'
    ]
  },
  {
    id: 'dazhou', name: '达州铁路分局公司', seedStationIds: ['xiyu_03','chengbaan_tongjiang'],
    boundaryEdgeIds: [
      'high_speed:bazhong_01|guangbada_pingchang',
      'high_speed:chengbaan_bazhongdong|chengbaan_tongjiang',
      'high_speed:chengdawan_quxianbei|chengdawan_yingshanxi',
      'high_speed:xiyu_dazu|xiyu_guangandong',
      'high_speed:xiyu_fankuai|xiyu_kaizhou',
      'high_speed:chengdawan_kaijiang|chengdawan_kaizhounan',
      'high_speed:chengbaan_wanyuanbei|chengbaan_ziyangnan',
      'high_speed:xiyu_chengkou|xiyu_langao'
    ]
  },
  {
    id: 'wanzhou', name: '万州铁路分局公司', seedStationId: 'yiwan_wanzhou',
    boundaryEdgeIds: [
      'high_speed:xiyu_fankuai|xiyu_kaizhou',
      'high_speed:chengdawan_kaijiang|chengdawan_kaizhounan',
      'high_speed:yuwan_dianjiang|yuwan_liangpingnan',
      'high_speed:yuwan_fengdubei|yuwan_zhongxian',
      'high_speed:wanqian_shizhu|yuxia_pengshuixi',
      'high_speed:zhengyu_badong|zhengyu_wushan',
      'conventional:yiwan_lichuan|yiwan_wanzhou'
    ]
  },
  {
    id: 'yibin', name: '宜宾铁路分局公司', seedStationIds: ['chengyi_yibin','yukun_hejiang'],
    boundaryEdgeIds: [
      'high_speed:chengyi_weiyuan|chengyi_zizhongxi',
      'high_speed:chengyu_03|chengziyi_03',
      'high_speed:chenggui_nixi|chenggui_qianwei',
      'conventional:yixipan_leibo|yixipan_suijiang',
      'high_speed:yukun_luzhoudong|yukun_yongchuannan',
      'high_speed:yukun_baisha|yukun_hejiang',
      'high_speed:chenggui_weixin|chenggui_xingwen',
      'high_speed:yukun_junlian|yukun_yanjinnan',
      'high_speed:chenggui_05|yukun_gulin'
    ]
  },
  {
    id: 'guiyang', name: '贵阳铁路分局公司', seedStationId: 'qiangui_guiyang',
    boundaryEdgeIds: [
      'high_speed:yugui_qijiangdong|yugui_tongzidong',
      'high_speed:yugui2_wansheng|yugui2_zhengan',
      'high_speed:chenggui_dafang|chenggui_qianxi',
      'high_speed:anliu_liuzhinan|hukun_19',
      'high_speed:hukun_guanling|hukun_puanxian',
      'high_speed:hukun_tongrennan|hukun_xinhuangxi',
      'high_speed:guinan_huanjiang|guinan_libo',
      'high_speed:guigang_congjiang|guigang_sanjiangnan',
      'conventional:qiangui_dushan|qiangui_nandan'
    ]
  },
  {
    id: 'liupanshui', name: '六盘水铁路分局公司', seedStationId: 'anliu_05',
    boundaryEdgeIds: [
      'high_speed:chenggui_weixin|chenggui_xingwen',
      'high_speed:chenggui_05|yukun_gulin',
      'high_speed:chenggui_dafang|chenggui_qianxi',
      'high_speed:anliu_liuzhinan|hukun_19',
      'high_speed:hukun_guanling|hukun_puanxian',
      'high_speed:yukun_04|zhaoliu_weining',
      'high_speed:anliu_05|liukun_xuanwei',
      'high_speed:hukun_fuyuanbei|hukun_panzhou',
      'high_speed:xingbai_ceheng|xingbai_tianlin',
      'conventional:nankun_luoping|nankun_weishe'
    ]
  },
  {
    id: 'kunming', name: '昆明铁路分局公司', seedStationId: 'chengkun_kunming',
    boundaryEdgeIds: [
      'high_speed:yukun_junlian|yukun_yanjinnan',
      'conventional:chengkun_03|chengkun_yongren',
      'high_speed:yukun_04|zhaoliu_weining',
      'high_speed:anliu_05|liukun_xuanwei',
      'high_speed:hukun_fuyuanbei|hukun_panzhou',
      'conventional:chengkun_nanhua|chengkun_xiangyun',
      'conventional:kunmo_02|kunmo_jinningdong',
      'conventional:nankun_mile|yumi_huaning',
      'high_speed:mimeng_zhuyuan|nankun_mile',
      'high_speed:nankun_02|nankun_funing',
      'conventional:nankun_luoping|nankun_weishe'
    ]
  },
  {
    id: 'dali', name: '大理铁路分局公司', seedStationId: 'diancang_03',
    boundaryEdgeIds: [
      'conventional:chengkun_nanhua|chengkun_xiangyun',
      'conventional:dianzang_deqin|dianzang_yanjing'
    ]
  },
  {
    id: 'yuxi', name: '玉溪铁路分局公司', seedStationId: 'kunmo_02',
    boundaryEdgeIds: [
      'conventional:kunmo_02|kunmo_jinningdong',
      'conventional:nankun_mile|yumi_huaning',
      'high_speed:mimeng_zhuyuan|nankun_mile'
    ]
  },
  {
    id: 'nanning', name: '南宁铁路分局公司', seedStationId: 'nankun_nanning',
    boundaryEdgeIds: [
      'high_speed:nankun_02|nankun_funing',
      'high_speed:xingbai_ceheng|xingbai_tianlin',
      'high_speed:guibai_bama|guibai_donglan',
      'high_speed:guinan_duan|yunan_05',
      'high_speed:liunan_binyang|nanheng_05',
      'high_speed:nanguang_05|nanguang_tengxian',
      'high_speed:shennan_cenxidong|shennan_rongxiannan',
      'high_speed:guitan_luchuan|nanzhan_lianjiangnan',
      'high_speed:nanzhan_baishazhen|nanzhan_lianjiangnan'
    ]
  },
  {
    id: 'liuzhou', name: '柳州铁路分局公司', seedStationId: 'nanheng_04',
    boundaryEdgeIds: [
      'high_speed:guinan_huanjiang|guinan_libo',
      'conventional:qiangui_dushan|qiangui_nandan',
      'high_speed:guibai_bama|guibai_donglan',
      'high_speed:guinan_duan|yunan_05',
      'high_speed:liunan_binyang|nanheng_05',
      'high_speed:hengliu_luzhaibei|hengliu_yongfunan',
      'high_speed:guibai_rongandong|guibai_yongfu',
      'high_speed:liuhe_huangyao|liuhe_zhaoping',
      'conventional:liuwu_tengxianbei|liuwu_wuzhou',
      'conventional:jiaoliu_sanjiangxian|jiaoliu_tongdao'
    ]
  },
  {
    id: 'guilin', name: '桂林铁路分局公司', seedStationId: 'hengliu_guilin',
    boundaryEdgeIds: [
      'high_speed:guigang_congjiang|guigang_sanjiangnan',
      'high_speed:hengliu_luzhaibei|hengliu_yongfunan',
      'high_speed:guibai_rongandong|guibai_yongfu',
      'high_speed:liuhe_huangyao|liuhe_zhaoping',
      'conventional:liuwu_tengxianbei|liuwu_wuzhou',
      'high_speed:nanguang_05|nanguang_tengxian',
      'high_speed:shennan_cenxidong|shennan_rongxiannan',
      'high_speed:guigang_04|guigang_huaiji',
      'high_speed:nanguang_05|nanguang_yunan',
      'high_speed:shennan_cenxidong|shennan_luodingbei',
      'high_speed:nanheng_lingling|nanheng_quanzhounan',
      'high_speed:huaigui_xinning|huaigui_ziyuan',
      'high_speed:guichen_guanyang|guichen_jiangyongbei'
    ]
  },
  {
    id: 'guangzhou', name: '广州铁路分局公司',
    seedStationIds: ['jingguang_24', 'guangshan_zengcheng'],
    boundaryEdgeIds: [
      'high_speed:guangshen_humen|guangshen_qingsheng',
      'high_speed:guangshen2_dongguanzhongxin|guangshen2_huangpu',
      'high_speed:shennan_binhaiwan|shennan_nansha',
      'high_speed:guangzhu_zhuhaibei|shennan_shenzhenxili',
      'high_speed:guangshan_luofushan|guangshan_zengcheng',
      'high_speed:guanghe_conghua|guanghe_yonghan',
      'high_speed:jingguang_21|jingguang_lechangdong',
      'high_speed:guangqingyong_lanshan|guangqingyong_lianzhou',
      'high_speed:ganguang_lianping|ganguang_quannan',
      'conventional:ganshao_dayu|ganshao_nanxiong',
      'high_speed:guigang_04|guigang_huaiji',
      'high_speed:nanguang_05|nanguang_yunan',
      'high_speed:shennan_cenxidong|shennan_luodingbei',
      'high_speed:guangzhan_xinxingnan|guangzhan_yangchundong',
      'high_speed:guangzhan_03|shenzhan_enping'
    ]
  },
  {
    id: 'shenzhen', name: '深圳铁路分局公司', seedStationId: 'heshen_10',
    boundaryEdgeIds: [
      'high_speed:guangshen_humen|guangshen_qingsheng',
      'high_speed:guangshen2_dongguanzhongxin|guangshen2_huangpu',
      'high_speed:shennan_binhaiwan|shennan_nansha',
      'high_speed:guangzhu_zhuhaibei|shennan_shenzhenxili',
      'high_speed:guangshan_luofushan|guangshan_zengcheng',
      'high_speed:guanghe_conghua|guanghe_yonghan',
      'high_speed:ganshen_dingnannan|ganshen_hepingbei',
      'high_speed:ganshen_longchuanxi|meilong_wuhua',
      'high_speed:guangshan_shenshan|hangshen_13',
      'high_speed:hangshen_13|xiashen_houmen'
    ]
  },
  {
    id: 'shantou', name: '汕头铁路分局公司', seedStationId: 'shanshan_shantou',
    boundaryEdgeIds: [
      'high_speed:ganshen_longchuanxi|meilong_wuhua',
      'high_speed:guangshan_shenshan|hangshen_13',
      'high_speed:hangshen_13|xiashen_houmen',
      'high_speed:zhangshan_raopingnan|zhangshan_zhaoannan',
      'conventional:longlong_jiaoling|longlong_wuping',
      'conventional:ruimei_pingyuan|ruimei_xunwu'
    ]
  },
  {
    id: 'zhanjiang', name: '湛江铁路分局公司', seedStationId: 'nanzhan_zhanjiangxi',
    boundaryEdgeIds: [
      'high_speed:nanzhan_baishazhen|nanzhan_lianjiangnan',
      'high_speed:guitan_luchuan|nanzhan_lianjiangnan',
      'high_speed:guangzhan_xinxingnan|guangzhan_yangchundong',
      'high_speed:guangzhan_03|shenzhan_enping',
      'high_speed:zhanhai_02|zhanhai_xuwennan'
    ]
  },
  {
    id: 'haikou', name: '海口铁路分局公司', seedStationId: 'zhanhai_02',
    boundaryEdgeIds: [
      'high_speed:zhanhai_02|zhanhai_xuwennan'
    ]
  }
];

window.resolveRailwayDivisions = function(data, definitions) {
  const distanceKm = (a,b) => {
    const radians=Math.PI/180;
    const h=Math.sin((b.lat-a.lat)*radians/2)**2+Math.cos(a.lat*radians)*Math.cos(b.lat*radians)*Math.sin((b.lon-a.lon)*radians/2)**2;
    return 6371.0088*2*Math.asin(Math.sqrt(Math.min(1,Math.max(0,h))));
  };
  const stations = new Map(data.stations.map(s=>[s.id,s]));
  const edges = new Map(data.connections.map(e=>[e.id,e]));
  const adjacent = new Map(data.stations.map(s=>[s.id,[]]));
  data.connections.forEach(e=>{ adjacent.get(e.from).push(e); adjacent.get(e.to).push(e); });
  const results = definitions.map(def=>{
    const blocked = new Set(def.boundaryEdgeIds), errors=[];
    const seedStationIds = def.seedStationIds || [def.seedStationId];
    if(!seedStationIds.length || seedStationIds.some(id=>!stations.has(id))) errors.push('中心站不存在');
    for(const id of blocked) if(!edges.has(id)) errors.push(`交界连接不存在：${id}`);
    const stationIds = new Set(), queue=[];
    if(!errors.length) { for(const id of seedStationIds) { stationIds.add(id); queue.push(id); } }
    for(const id of queue) for(const e of adjacent.get(id)) {
      if(blocked.has(e.id)) continue;
      const next=e.from===id?e.to:e.from;
      if(!stationIds.has(next)) { stationIds.add(next); queue.push(next); }
    }
    const boundaries=[];
    for(const id of blocked) {
      const e=edges.get(id); if(!e) continue;
      if(stationIds.has(e.from)===stationIds.has(e.to)) { errors.push('交界未能隔开内外两侧，请检查绕行连接'); continue; }
      const from=stations.get(e.from),to=stations.get(e.to);
      boundaries.push({edgeId:id,insideId:stationIds.has(e.from)?e.from:e.to,outsideId:stationIds.has(e.from)?e.to:e.from,
        lat:(from.lat+to.lat)/2,lon:(from.lon+to.lon)/2});
    }
    const edgeIds=new Set(data.connections.filter(e=>!blocked.has(e.id)&&stationIds.has(e.from)&&stationIds.has(e.to)).map(e=>e.id));
    const lengthKm={high_speed:0,conventional:0};
    for(const id of edgeIds) {
      const e=edges.get(id);lengthKm[e.type]+=distanceKm(stations.get(e.from),stations.get(e.to));
    }
    for(const b of boundaries) lengthKm[edges.get(b.edgeId).type]+=distanceKm(stations.get(b.insideId),b);
    return {...def,stationIds,edgeIds,boundaries,lengthKm,errors};
  });
  // 后续划分多家分局时，不允许重复归属悄悄覆盖。
  for(let i=0;i<results.length;i++) for(let j=i+1;j<results.length;j++) {
    if([...results[i].stationIds].some(id=>results[j].stationIds.has(id))) {
      results[i].errors.push(`与${results[j].name}的站点归属重叠`);
      results[j].errors.push(`与${results[i].name}的站点归属重叠`);
    }
  }
  return results;
};
