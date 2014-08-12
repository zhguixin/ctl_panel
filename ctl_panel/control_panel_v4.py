#!/usr/bin/env python
#coding=utf-8
#################################
#   Copyright 2014.6.10
#       fly_vedio 
#   @author: 345570600@qq.com
#################################
import wx
import wx.grid
import sys
import threading  
import socket,select
import json
import time
import Queue
import ConfigParser
from wx.lib.pubsub import Publisher 

#设置系统默认编码方式，不用下面两句，中文会乱码
reload(sys)  
sys.setdefaultencoding("utf-8")

#定义一些全局变量
param = {}

class Terminal(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        #创建面板
        self.CreatePanel()

    def CreatePanel(self):

        #参数从文件中读取并初始化，如果初始文件不存在这个参数的值则用默认值
        try: s_u_frequency = self.param_config.getint("Terminal", "s_u_frequency")
        except: s_u_frequency = 1985

        try: s_d_frequency = self.param_config.getint("Terminal", "s_d_frequency")
        except: s_d_frequency = 2185

        try: s_m_part = self.param_config.get("Terminal", "s_m_part")
        except: s_m_part = '2'

        try: s_bigm_part = self.param_config.get("Terminal", "s_bigm_part")
        except: s_bigm_part = '2'

        try: s_threshold = self.param_config.get("Terminal", "s_threshold")
        except: s_threshold = '0.85'

        #上行中心频率
        u_frequency_st = wx.StaticText(self, -1, u"上行中心频率:")
        self.u_frequency = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.u_frequency.SetRange(1980,2010)
        self.u_frequency.SetValue(s_u_frequency)

        #下行中心频率
        d_frequency_st = wx.StaticText(self, -1, u"下行中心频率:")
        self.d_frequency = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.d_frequency.SetRange(2170,2200)
        self.d_frequency.SetValue(s_d_frequency)

        # m_part优化算法插零数
        m_part_list = ['1','2','4']
        m_part_st = wx.StaticText(self, -1, u"m_part优化算法插零数:")
        self.m_part = wx.ComboBox(self, -1, s_m_part, wx.DefaultPosition, wx.DefaultSize, m_part_list, 0)

        # M_part算法分段数
        M_part_list = ['1','2','4','8']
        M_part_st = wx.StaticText(self, -1, u"M_part算法分段数:")
        self.M_part = wx.ComboBox(self, -1, s_bigm_part, wx.DefaultPosition, wx.DefaultSize, M_part_list, 0)

        #阈值
        Threshold_st = wx.StaticText(self, -1, u"阈值:")
        self.Threshold = wx.TextCtrl(self, -1, s_threshold)

        #高级按钮
        self.senior_button = wx.Button(self, -1, u"高级")
        self.senior_button.SetBackgroundColour('black')
        self.senior_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Senior,self.senior_button)

        #######开始布局############
        #参数窗口
        sizer2 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer2.AddGrowableCol(1)
        sizer2.Add(u_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.u_frequency, 0, wx.EXPAND)
        sizer2.Add(d_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.d_frequency, 0, wx.EXPAND)
        sizer2.Add(m_part_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.m_part, 0, wx.EXPAND)
        sizer2.Add(M_part_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.M_part, 0, wx.EXPAND)
        sizer2.Add(Threshold_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Threshold, 0, wx.EXPAND)

        #高级按钮
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add((20,20), 1)
        sizer3.Add(self.senior_button, 0, wx.ALIGN_RIGHT)

        #添加参数子块，带边框的模块布局，包含参数和高级按钮
        sizer1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'重要参数'), wx.VERTICAL)
        sizer1.Add(sizer2, 0, wx.EXPAND | wx.ALL, 15)
        # sizer1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        #box1垂直布局,box1即左半界面
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)
        box1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 5)

        #自动调整界面尺寸
        self.SetSizer(box1)
        box1.Fit(self)
        box1.SetSizeHints(self)

    def Senior(self,event):
        self.seniordialog = SeniorDialog_Terminal(None)
        self.seniordialog.ok_button.Bind(wx.EVT_BUTTON, self.OnOk)
        self.seniordialog.Show()
        # self.seniordialog.ShowModal()

    def OnOk(self,event):
        #将设置好的参数写入配置文件
        self.param_config.read("param.conf")
        if "Terminal" not in self.param_config.sections():
            self.param_config.add_section("Terminal")

        self.param_config.set("Terminal", "s_rnti_a", self.seniordialog.RNTI_A.GetValue())
        self.param_config.set("Terminal", "s_rnti_b", self.seniordialog.RNTI_B.GetValue())
        self.param_config.set("Terminal", "s_t_advance_a", self.seniordialog.t_advance_A.GetValue())
        self.param_config.set("Terminal", "s_t_advance_b", self.seniordialog.t_advance_B.GetValue())
        self.param_config.set("Terminal", "s_n_pucch_a", self.seniordialog.n_pucch_A.GetValue())
        self.param_config.set("Terminal", "s_n_pucch_b", self.seniordialog.n_pucch_B.GetValue())
        self.param_config.set("Terminal", "s_data_rules", self.seniordialog.data_rules.GetValue())
        self.param_config.set("Terminal", "s_iter_num", self.seniordialog.iter_num.GetValue())
        self.param_config.set("Terminal", "s_delta_ss", self.seniordialog.Delta_ss.GetValue())
        self.param_config.set("Terminal", "s_shift", self.seniordialog.shift.GetValue())
        self.param_config.set("Terminal", "s_DMRS1", self.seniordialog.DMRS1.GetValue())
        self.param_config.set("Terminal", "s_decision_type", self.seniordialog.decision_type.GetValue())
        self.param_config.set("Terminal", "s_algorithm_c", self.seniordialog.algorithm_c.GetValue())
        self.param_config.set("Terminal", "s_gain_r_sc", self.seniordialog.Gain_r_sc.GetValue())
        self.param_config.set("Terminal", "s_gain_s_sc", self.seniordialog.Gain_s_sc.GetValue())
        self.param_config.set("Terminal", "s_samp_rate_sc", self.seniordialog.samp_rate_c.GetValue())
        self.param_config.set("Terminal", "s_c_srs_a", self.seniordialog.C_SRS_A.GetValue())
        self.param_config.set("Terminal", "s_b_srs_a", self.seniordialog.B_SRS_A.GetValue())
        self.param_config.set("Terminal", "s_n_srs_a", self.seniordialog.n_SRS_A.GetValue())
        self.param_config.set("Terminal", "s_n_rrc_a", self.seniordialog.n_RRC_A.GetValue())
        self.param_config.set("Terminal", "s_k_tc_a", self.seniordialog.K_TC_A.GetValue())
        self.param_config.set("Terminal", "s_srs_period_a", self.seniordialog.SRS_period_A.GetValue())
        self.param_config.set("Terminal", "s_srs_offset_a", self.seniordialog.SRS_offset_A.GetValue())
        self.param_config.set("Terminal", "s_sr_periodicity_a", self.seniordialog.SR_periodicity_A.GetValue())
        self.param_config.set("Terminal", "s_sr_offset_a", self.seniordialog.SR_offset_A.GetValue())
        self.param_config.set("Terminal", "s_c_srs_b", self.seniordialog.C_SRS_B.GetValue())
        self.param_config.set("Terminal", "s_b_srs_b", self.seniordialog.B_SRS_B.GetValue())
        self.param_config.set("Terminal", "s_n_srs_b", self.seniordialog.n_SRS_B.GetValue())
        self.param_config.set("Terminal", "s_n_rrc_b", self.seniordialog.n_RRC_B.GetValue())
        self.param_config.set("Terminal", "s_k_tc_b", self.seniordialog.K_TC_B.GetValue())
        self.param_config.set("Terminal", "s_srs_period_b", self.seniordialog.SRS_period_B.GetValue())
        self.param_config.set("Terminal", "s_srs_offset_b", self.seniordialog.SRS_offset_B.GetValue())
        self.param_config.set("Terminal", "s_sr_periodicity_b", self.seniordialog.SR_periodicity_B.GetValue())
        self.param_config.set("Terminal", "s_sr_offset_b", self.seniordialog.SR_offset_B.GetValue())
        self.param_config.set("Terminal", "s_t_reordering", self.seniordialog.t_Reordering.GetValue())
        self.param_config.set("Terminal", "s_t_statusprohibit", self.seniordialog.t_StatusProhibit.GetValue())
        self.param_config.set("Terminal", "s_t_pollretransmit", self.seniordialog.t_PollRetransmit.GetValue())
        self.param_config.set("Terminal", "s_maxretxthreshold", self.seniordialog.maxRetxThreshold.GetValue())
        self.param_config.set("Terminal", "s_sn_fieldlength", self.seniordialog.SN_FieldLength.GetValue())
        self.param_config.set("Terminal", "s_pollpdu", self.seniordialog.pollPDU.GetValue())
        self.param_config.set("Terminal", "s_pollbyte", self.seniordialog.pollByte.GetValue())
        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        self.seniordialog.Destroy()

class SeniorDialog_Terminal(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, title=u'终端高级配置')
        self.parent = parent
        # self.SetTitle(u'终端高级配置')
        self.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        #创建面板
        self.SeniorPanel()

    def SeniorPanel(self):

        #参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_rnti_a = self.param_config.getint("Terminal", "s_rnti_a")
        except: s_rnti_a = 100

        try: s_rnti_b = self.param_config.getint("Terminal", "s_rnti_b")
        except: s_rnti_b = 200

        try: s_t_advance_a = self.param_config.get("Terminal", "s_t_advance_a")
        except: s_t_advance_a = '0'

        try: s_t_advance_b = self.param_config.get("Terminal", "s_t_advance_b")
        except: s_t_advance_b = '0'

        try: s_n_pucch_a = self.param_config.get("Terminal", "s_n_pucch_a")
        except: s_n_pucch_a = '0'

        try: s_n_pucch_b = self.param_config.get("Terminal", "s_n_pucch_b")
        except: s_n_pucch_b = '18'

        try: s_data_rules = self.param_config.get("Terminal", "s_data_rules")
        except: s_data_rules = '规则递增'

        try: s_iter_num = self.param_config.getint("Terminal", "s_iter_num")
        except: s_iter_num = 4

        try: s_delta_ss = self.param_config.getint("Terminal", "s_delta_ss")
        except: s_delta_ss = 10

        try: s_shift = self.param_config.getint("Terminal", "s_shift")
        except: s_shift = 1

        try: s_DMRS1 = self.param_config.get("Terminal", "s_DMRS1")
        except: s_DMRS1 = '4'

        try: s_decision_type = self.param_config.get("Terminal", "s_decision_type")
        except: s_decision_type = 'soft'

        try: s_algorithm_c = self.param_config.get("Terminal", "s_algorithm_c")
        except: s_algorithm_c = 'Max_Log'

        try: s_gain_r_sc = self.param_config.getint("Terminal", "s_gain_r_sc")
        except: s_gain_r_sc = 10

        try: s_gain_s_sc = self.param_config.getint("Terminal", "s_gain_s_sc")
        except: s_gain_s_sc = 10

        try: s_samp_rate_sc = self.param_config.get("Terminal", "s_samp_rate_sc")
        except: s_samp_rate_sc = '2M'

        try: s_c_srs_a = self.param_config.getint("Terminal", "s_c_srs_a")
        except: s_c_srs_a = 4

        try: s_b_srs_a = self.param_config.getint("Terminal", "s_b_srs_a")
        except: s_b_srs_a = 1

        try: s_n_srs_a = self.param_config.getint("Terminal", "s_n_srs_a")
        except: s_n_srs_a = 4

        try: s_n_rrc_a = self.param_config.getint("Terminal", "s_n_rrc_a")
        except: s_n_rrc_a = 0

        try: s_k_tc_a = self.param_config.get("Terminal", "s_k_tc_a")
        except: s_k_tc_a = '0'

        try: s_srs_period_a = self.param_config.get("Terminal", "s_srs_period_a")
        except: s_srs_period_a = '2'

        try: s_srs_offset_a = self.param_config.get("Terminal", "s_srs_offset_a")
        except: s_srs_offset_a = '0'

        try: s_sr_periodicity_a = self.param_config.get("Terminal", "s_sr_periodicity_a")
        except: s_sr_periodicity_a = '10'

        try: s_sr_offset_a = self.param_config.get("Terminal", "s_sr_offset_a")
        except: s_sr_offset_a = '2'

        try: s_k_tc_b = self.param_config.get("Terminal", "s_k_tc_b")
        except: s_k_tc_b = '1'

        try: s_srs_period_b = self.param_config.get("Terminal", "s_srs_period_b")
        except: s_srs_period_b = '2'

        try: s_srs_offset_b = self.param_config.get("Terminal", "s_srs_offset_b")
        except: s_srs_offset_b = '1'

        try: s_sr_periodicity_b= self.param_config.get("Terminal", "s_sr_periodicity_b")
        except: s_sr_periodicity_b = '10'

        try: s_sr_offset_b = self.param_config.get("Terminal", "s_sr_offset_b")
        except: s_sr_offset_b = '4'

        try: s_c_srs_b = self.param_config.getint("Terminal", "s_c_srs_b")
        except: s_c_srs_b = 4

        try: s_b_srs_b = self.param_config.getint("Terminal", "s_b_srs_b")
        except: s_b_srs_b = 1

        try: s_n_srs_b = self.param_config.getint("Terminal", "s_n_srs_b")
        except: s_n_srs_b = 4

        try: s_n_rrc_b = self.param_config.getint("Terminal", "s_n_rrc_b")
        except: s_n_rrc_b = 0

        try: s_t_reordering = self.param_config.getint("Terminal", "s_t_reordering")
        except: s_t_reordering = 40

        try: s_t_statusprohibit = self.param_config.getint("Terminal", "s_t_statusprohibit")
        except: s_t_statusprohibit = 40

        try: s_t_pollretransmit = self.param_config.getint("Terminal", "s_t_pollretransmit")
        except: s_t_pollretransmit = 40

        try: s_maxretxthreshold = self.param_config.get("Terminal", "s_maxretxthreshold")
        except: s_maxretxthreshold = '4'

        try: s_sn_fieldlength = self.param_config.get("Terminal", "s_sn_fieldlength")
        except: s_sn_fieldlength = '10'

        try: s_pollpdu = self.param_config.get("Terminal", "s_pollpdu")
        except: s_pollpdu = '16'

        try: s_pollbyte = self.param_config.get("Terminal", "s_pollbyte")
        except: s_pollbyte = '125'

        #终端A的RNTI，两个终端单独配置
        RNTI_st_A = wx.StaticText(self, -1, u"RNTI:")
        self.RNTI_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.RNTI_A.SetRange(61,65523)
        self.RNTI_A.SetValue(s_rnti_a)

        #终端B的RNTI，两个终端单独配置
        RNTI_st_B = wx.StaticText(self, -1, u"RNTI:")
        self.RNTI_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.RNTI_B.SetRange(61,65523)
        self.RNTI_B.SetValue(s_rnti_b)

        #终端A的时间提前量，终端与信关站之间的单向传播时延；两个终端单独配置 
        t_advance_st_A = wx.StaticText(self, -1, u"时间提前量:")
        self.t_advance_A = wx.TextCtrl(self, -1, s_t_advance_a)

        #终端B的时间提前量，终端与信关站之间的单向传播时延；两个终端单独配置 
        t_advance_st_B = wx.StaticText(self, -1, u"时间提前量:")
        self.t_advance_B = wx.TextCtrl(self, -1, s_t_advance_b)

        #用户A资源索引，两个终端单独配置
        n_pucch_A_st = wx.StaticText(self, -1, u"资源索引:")
        self.n_pucch_A = wx.TextCtrl(self, -1, s_n_pucch_a)

        #用户B资源索引，两个终端单独配置
        n_pucch_B_st = wx.StaticText(self, -1, u"资源索引:")
        self.n_pucch_B = wx.TextCtrl(self, -1, s_n_pucch_b)

        #C_SRS由高层的srs-BandwidthConfig参数得到，终端A用此参数确定序列的长度
        C_SRS_A_st = wx.StaticText(self, -1, "C_SRS:")
        self.C_SRS_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.C_SRS_A.SetRange(0,7)
        self.C_SRS_A.SetValue(s_c_srs_a)

        #C_SRS由高层的srs-BandwidthConfig参数得到，终端B用此参数确定序列的长度
        C_SRS_B_st = wx.StaticText(self, -1, "C_SRS:")
        self.C_SRS_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.C_SRS_B.SetRange(0,7)
        self.C_SRS_B.SetValue(s_c_srs_b)

        #由高层的srs-Bandwidth参数得到，终端A用此参数确定序列的长度
        B_SRS_A_st = wx.StaticText(self, -1, "B_SRS:")
        self.B_SRS_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.B_SRS_A.SetRange(0,3)
        self.B_SRS_A.SetValue(s_b_srs_a)

        #由高层的srs-Bandwidth参数得到，终端B用此参数确定序列的长度
        B_SRS_B_st = wx.StaticText(self, -1, "B_SRS:")
        self.B_SRS_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.B_SRS_B.SetRange(0,3)
        self.B_SRS_B.SetValue(s_b_srs_b)

        #由高层cyclicshift参数得到 ，终端A用此参数确定序列的循环移位
        n_SRS_A_st = wx.StaticText(self, -1, "n_SRS:")
        self.n_SRS_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_SRS_A.SetRange(0,7)
        self.n_SRS_A.SetValue(s_n_srs_a)

        #由高层cyclicshift参数得到 ，终端B用此参数确定序列的循环移位
        n_SRS_B_st = wx.StaticText(self, -1, "n_SRS:")
        self.n_SRS_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_SRS_B.SetRange(0,7)
        self.n_SRS_B.SetValue(s_n_srs_b)

        #终端A的K_TC,两个终端分别配置
        K_TC_A_list = ['0', '1']
        K_TC_A_st = wx.StaticText(self, -1, u"K_TC:")
        self.K_TC_A = wx.ComboBox(self, -1, s_k_tc_a, wx.DefaultPosition, wx.DefaultSize, K_TC_A_list, 0)

        #终端B的K_TC,两个终端分别配置
        K_TC_B_list = ['0', '1']
        K_TC_B_st = wx.StaticText(self, -1, u"K_TC:")
        self.K_TC_B = wx.ComboBox(self, -1, s_k_tc_b, wx.DefaultPosition, wx.DefaultSize, K_TC_B_list, 0)

        #终端A的SRS周期，终端分别配置
        SRS_period_A_list = ['1','2','5','10']
        SRS_period_A_st = wx.StaticText(self, -1, u"SRS_period:")
        self.SRS_period_A = wx.ComboBox(self, -1, s_srs_period_a, wx.DefaultPosition, wx.DefaultSize, SRS_period_A_list, 0)
        
        #终端B的SRS周期，终端分别配置
        SRS_period_B_list = ['1','2','5','10']
        SRS_period_B_st = wx.StaticText(self, -1, u"SRS_period:")
        self.SRS_period_B = wx.ComboBox(self, -1, s_srs_period_b, wx.DefaultPosition, wx.DefaultSize, SRS_period_B_list, 0)
        
        #终端A的SRS补偿，终端分别配置
        SRS_offset_A_list = ['0','1','2','3','4','5','6','8']
        SRS_offset_A_st = wx.StaticText(self, -1, u"SRS_offset:")
        self.SRS_offset_A = wx.ComboBox(self, -1, s_srs_offset_a, wx.DefaultPosition, wx.DefaultSize, SRS_offset_A_list, 0)
        
        #终端B的SRS补偿，终端分别配置
        SRS_offset_B_list = ['0','1','2','3','4','5','6','8']
        SRS_offset_B_st = wx.StaticText(self, -1, u"SRS_offset:")
        self.SRS_offset_B = wx.ComboBox(self, -1, s_srs_offset_b, wx.DefaultPosition, wx.DefaultSize, SRS_offset_B_list, 0)
        
        #终端A的SR周期，终端分别配置
        SR_periodicity_A_list = ['5','10','20','40','80','2','1']
        SR_periodicity_A_st = wx.StaticText(self, -1, u"SR_periodicity:")
        self.SR_periodicity_A = wx.ComboBox(self, -1, s_sr_periodicity_a, wx.DefaultPosition, wx.DefaultSize, SR_periodicity_A_list, 0)
        
        #终端B的SR周期，终端分别配置
        SR_periodicity_B_list = ['5','10','20','40','80','2','1']
        SR_periodicity_B_st = wx.StaticText(self, -1, u"SR_periodicity:")
        self.SR_periodicity_B = wx.ComboBox(self, -1, s_sr_periodicity_b, wx.DefaultPosition, wx.DefaultSize, SR_periodicity_B_list, 0)
        
        #终端A的SR补偿，终端分别配置
        SR_offset_A_st = wx.StaticText(self, -1, u"SR_offset:")
        self.SR_offset_A = wx.TextCtrl(self, -1, s_sr_offset_a)

        #终端B的SR补偿，终端分别配置
        SR_offset_B_st = wx.StaticText(self, -1, u"SR_offset:")
        self.SR_offset_B = wx.TextCtrl(self, -1, s_sr_offset_b)

        #由高层freqDomainPositon参数给出，终端A用此参数确定映射时的频带起始位置
        n_RRC_A_st = wx.StaticText(self, -1, "n_RRC:")
        self.n_RRC_A = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_RRC_A.SetRange(0,23)
        self.n_RRC_A.SetValue(s_n_rrc_a)

        #由高层freqDomainPositon参数给出，终端B用此参数确定映射时的频带起始位置
        n_RRC_B_st = wx.StaticText(self, -1, "n_RRC:")
        self.n_RRC_B = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.n_RRC_B.SetRange(0,23)
        self.n_RRC_B.SetValue(s_n_rrc_b)

        #测试数据生成规则
        data_rules_list = [u'规则递增', u'指定种子的随机序列']
        data_rules_st = wx.StaticText(self, -1, u"测试数据生成规则:")
        self.data_rules = wx.ComboBox(self, -1, s_data_rules, wx.DefaultPosition, wx.DefaultSize, data_rules_list, 0)

        #译码算法迭代次数
        iter_num_st = wx.StaticText(self, -1, u"译码算法迭代次数:")
        self.iter_num = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.iter_num.SetRange(1,8)
        self.iter_num.SetValue(s_iter_num)

        #用于配置fss
        Delta_ss_st = wx.StaticText(self, -1, u"Δss:")
        self.Delta_ss = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.Delta_ss.SetRange(0,29)
        self.Delta_ss.SetValue(s_delta_ss)

        #循环移位间隔
        shift_st = wx.StaticText(self, -1, u"循环移位间隔:")
        self.shift = wx.SpinCtrl(self, -1, "", (-1,-1))
        self.shift.SetRange(1,3)
        self.shift.SetValue(s_shift)

        #解调参考符号
        DMRS1_list = ['0', '2', '3', '4', '6', '8', '9', '10']
        DMRS1_st = wx.StaticText(self, -1, u"DMRS1:")
        self.DMRS1 = wx.ComboBox(self, -1, s_DMRS1, wx.DefaultPosition, wx.DefaultSize, DMRS1_list, 0)

        #判决方式
        decision_type_list = ['soft', 'hard']
        decision_type_st = wx.StaticText(self, -1, u"判决方式:")
        self.decision_type = wx.ComboBox(self, -1, s_decision_type, wx.DefaultPosition, wx.DefaultSize, decision_type_list, 0)

        #Turbo译码算法 
        algorithm_list = ['Max_Log',u'维特比']
        algorithm_st = wx.StaticText(self, -1 ,u"Turbo译码算法:")
        self.algorithm_c = wx.ComboBox(self, -1, s_algorithm_c, wx.DefaultPosition, wx.DefaultSize, algorithm_list, 0)

        #收发增益控制
        Gain_r_st = wx.StaticText(self, -1 ,u"接收增益(dB):")
        self.Gain_r_sc = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.Gain_r_sc.SetRange(0,30)
        self.Gain_r_sc.SetValue(s_gain_r_sc)

        Gain_s_st = wx.StaticText(self, -1, u"发送增益(dB):")
        self.Gain_s_sc = wx.SpinCtrl(self,-1, "",(-1, -1))
        self.Gain_s_sc.SetRange(0,20)
        self.Gain_s_sc.SetValue(s_gain_s_sc)

        #采样率
        samp_rate_list = ['2M','4M']
        samp_rate_st = wx.StaticText(self, -1 ,u"采样率:")
        self.samp_rate_c = wx.ComboBox(self, -1, s_samp_rate_sc, wx.DefaultPosition, wx.DefaultSize, samp_rate_list, 0)

        #由RLC UM的收端或AM使用，定时超时表明目前接收到但尚未递交高层的一段数据必须丢弃
        t_Reordering_st = wx.StaticText(self, -1, "t_Reordering(ms):")
        self.t_Reordering = wx.Slider(self, -1, s_t_reordering, 0, 200, size=(300, -1),
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        #设置滑块的刻度
        self.t_Reordering.SetTickFreq(5, 1)  
        #设置箭头调整的幅度
        self.t_Reordering.SetLineSize(10)
        #调整pageup/pagedown调整的幅度
        self.t_Reordering.SetPageSize(5)

        #由RLC AM使用，发送完一个状态报告之后，禁止再次发送的时间范围
        t_StatusProhibit_st = wx.StaticText(self, -1, "t_StatusProhibit(ms):")
        self.t_StatusProhibit = wx.Slider(self, -1, s_t_statusprohibit, 0, 500, 
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.t_StatusProhibit.SetTickFreq(10, 1) 
        self.t_StatusProhibit.SetLineSize(10)
        self.t_StatusProhibit.SetPageSize(5)

        #由RLC AM使用，发起状态查询，即主动请求对端发送状态报告的周期
        t_PollRetransmit_st = wx.StaticText(self, -1, "t_PollRetransmit(ms):")
        self.t_PollRetransmit = wx.Slider(self, -1, s_t_pollretransmit, 5, 500, 
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.t_PollRetransmit.SetTickFreq(10, 1) 
        self.t_PollRetransmit.SetLineSize(10)
        self.t_PollRetransmit.SetPageSize(5)

        #最大重传次数
        maxRetxThreshold_list = ['1', '2', '3', '4', '6', '8', '16', '32']
        maxRetxThreshold_st = wx.StaticText(self, -1, u"最大重传次数:")
        self.maxRetxThreshold = wx.ComboBox(self, -1, s_maxretxthreshold, wx.DefaultPosition, wx.DefaultSize, maxRetxThreshold_list, 0)

        #RLC UM使用，PDU中序号占用的比特数
        SN_FieldLength_list = ['5', '10']
        SN_FieldLength_st = wx.StaticText(self, -1, "SN_FieldLength:")
        self.SN_FieldLength = wx.ComboBox(self, -1, s_sn_fieldlength, wx.DefaultPosition, wx.DefaultSize, SN_FieldLength_list, 0)

        #RLC AM使用，当发送的PDU个数大于该计数器，强制启动状态查询
        pollPDU_list = ['4', '8', '16', '32', '64', '128', '256']
        pollPDU_st = wx.StaticText(self, -1, "pollPDU:")
        self.pollPDU = wx.ComboBox(self, -1, s_pollpdu, wx.DefaultPosition, wx.DefaultSize, pollPDU_list, 0)

        #RLC AM使用，当发送的SDU字节数大于该计数器，强制启动状态查询
        pollByte_list = ['25','50','75','100','125','250','375','500','750','1000','1250','1500','2000','3000']
        pollByte_st = wx.StaticText(self, -1, "pollByte(KB):")
        self.pollByte = wx.ComboBox(self, -1, s_pollbyte, wx.DefaultPosition, wx.DefaultSize, pollByte_list, 0)

        #确定设置按钮
        self.ok_button = wx.Button(self, -1, u"确定")
        self.ok_button.SetBackgroundColour('black')
        self.ok_button.SetForegroundColour('white')
        # self.ok_button.SetDefault()

        #帮助按钮
        self.help_button1 = wx.Button(self, -1, u"帮助1")
        self.help_button1.SetBackgroundColour('black')
        self.help_button1.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Help,self.help_button1)

        self.help_button2 = wx.Button(self, -1, u"帮助2")
        self.help_button2.SetBackgroundColour('black')
        self.help_button2.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Help_dialog2,self.help_button2)

        #MAC/PHY布局
        sizer2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        sizer2.AddGrowableCol(1)
        sizer2.Add(data_rules_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.data_rules, 0, wx.EXPAND)
        sizer2.Add(iter_num_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.iter_num, 0, wx.EXPAND)
        sizer2.Add(Delta_ss_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Delta_ss, 0, wx.EXPAND)
        sizer2.Add(shift_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.shift, 0, wx.EXPAND)
        sizer2.Add(DMRS1_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.DMRS1, 0, wx.EXPAND)
        sizer2.Add(decision_type_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.decision_type, 0, wx.EXPAND)
        sizer2.Add(algorithm_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.algorithm_c, 0, wx.EXPAND)
        sizer2.Add(Gain_r_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_r_sc, 0, wx.EXPAND)
        sizer2.Add(Gain_s_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_s_sc, 0, wx.EXPAND)
        sizer2.Add(samp_rate_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.samp_rate_c, 0, wx.EXPAND)

        #RLC布局
        sizer4 = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        sizer4.AddGrowableCol(1)
        sizer4.Add(t_Reordering_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_Reordering, 0, wx.EXPAND)
        sizer4.Add(t_StatusProhibit_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_StatusProhibit, 0, wx.EXPAND)
        sizer4.Add(t_PollRetransmit_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_PollRetransmit, 0, wx.EXPAND)
        sizer4.Add(maxRetxThreshold_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.maxRetxThreshold, 0, wx.EXPAND)
        sizer4.Add(SN_FieldLength_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.SN_FieldLength, 0, wx.EXPAND)
        sizer4.Add(pollPDU_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.pollPDU, 0, wx.EXPAND)
        sizer4.Add(pollByte_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.pollByte, 0, wx.EXPAND)

        #终端A布局
        sizerA = wx.FlexGridSizer(cols=4,hgap=5,vgap=5)
        sizerA.AddGrowableCol(1)
        sizerA.Add(RNTI_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.RNTI_A, 0, wx.EXPAND)
        sizerA.Add(C_SRS_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.C_SRS_A, 0, wx.EXPAND)
        sizerA.Add(B_SRS_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.B_SRS_A, 0, wx.EXPAND)
        sizerA.Add(n_SRS_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.n_SRS_A, 0, wx.EXPAND)
        sizerA.Add(n_RRC_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.n_RRC_A, 0, wx.EXPAND)
        sizerA.Add(K_TC_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.K_TC_A, 0, wx.EXPAND)
        sizerA.Add(SRS_period_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SRS_period_A, 0, wx.EXPAND)
        sizerA.Add(SRS_offset_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SRS_offset_A, 0, wx.EXPAND)
        sizerA.Add(SR_periodicity_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SR_periodicity_A, 0, wx.EXPAND)
        sizerA.Add(SR_offset_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.SR_offset_A, 0, wx.EXPAND)
        sizerA.Add(n_pucch_A_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.n_pucch_A, 0, wx.EXPAND)
        sizerA.Add(t_advance_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerA.Add(self.t_advance_A, 0, wx.EXPAND)

        #终端B布局
        sizerB = wx.FlexGridSizer(cols=4,hgap=5,vgap=5)
        sizerB.AddGrowableCol(1)
        sizerB.Add(RNTI_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.RNTI_B, 0, wx.EXPAND)
        sizerB.Add(C_SRS_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.C_SRS_B, 0, wx.EXPAND)
        sizerB.Add(B_SRS_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.B_SRS_B, 0, wx.EXPAND)
        sizerB.Add(n_SRS_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.n_SRS_B, 0, wx.EXPAND)
        sizerB.Add(n_RRC_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.n_RRC_B, 0, wx.EXPAND)
        sizerB.Add(K_TC_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.K_TC_B, 0, wx.EXPAND)
        sizerB.Add(SRS_period_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SRS_period_B, 0, wx.EXPAND)
        sizerB.Add(SRS_offset_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SRS_offset_B, 0, wx.EXPAND)
        sizerB.Add(SR_periodicity_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SR_periodicity_B, 0, wx.EXPAND)
        sizerB.Add(SR_offset_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.SR_offset_B, 0, wx.EXPAND)
        sizerB.Add(n_pucch_B_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.n_pucch_B, 0, wx.EXPAND)
        sizerB.Add(t_advance_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizerB.Add(self.t_advance_B, 0, wx.EXPAND)

        #确定按钮布局
        sizer31 = wx.BoxSizer(wx.HORIZONTAL)
        sizer31.Add((20,20), 1)
        sizer31.Add(self.ok_button, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        sizer31.Add(self.help_button1, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        sizer31.Add(self.help_button2, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        
        sizer3 = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add((120,180), 1)
        sizer3.Add(sizer31, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)

        #添加参数子块，带边框的模块布局
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'MAC/PHY层参数'), wx.VERTICAL)
        sizer5.Add(sizer2, 0, wx.EXPAND | wx.ALL, 10)

        sizer6 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'RLC层参数'), wx.VERTICAL)
        sizer6.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        sizer7 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'终端A'), wx.VERTICAL)
        sizer7.Add(sizerA, 0, wx.EXPAND | wx.ALL, 10)

        sizer8 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'终端B'), wx.VERTICAL)
        sizer8.Add(sizerB, 0, wx.EXPAND | wx.ALL, 10)

        sizer9 = wx.BoxSizer(wx.VERTICAL)
        sizer9.Add(sizer7, 0, wx.EXPAND | wx.ALL, 10)
        sizer9.Add(sizer8, 0, wx.EXPAND | wx.ALL, 10)
        sizer9.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(sizer5, 0, wx.EXPAND | wx.ALL, 10)
        sizer1.Add(sizer6, 0, wx.EXPAND | wx.ALL, 10)

        sizer10 = wx.BoxSizer(wx.HORIZONTAL)
        sizer10.Add(sizer1, 0, wx.EXPAND | wx.ALL, 5)
        sizer10.Add(sizer9, 0, wx.EXPAND | wx.ALL, 5)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer10, 0, wx.EXPAND | wx.ALL, 5)

        #自动调整界面尺寸
        self.SetSizer(box)
        box.Fit(self)
        box.SetSizeHints(self)

    def Help(self,event):
        self.dialog = Help_Dialog(self)
        # self.dialog.ShowModal()
        self.dialog.Show()

    def Help_dialog2(self,event):
        dlg = wx.MessageDialog(None, "根据标准TS36.211   Table 5.5.3.2-1\t\n\
        当链路带宽为1.4M，C_SRS、B_SRS、n_RRC的值应分别设置为：4、1、0\n\t当链路带宽为3M，C_SRS、B_SRS、n_RRC的值应分别设置为：0、1、0",
                          '帮助',
                          wx.OK | wx.ICON_INFORMATION)
        retCode = dlg.ShowModal()

class Gateway_station(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        #创建面板
        self.CreatePanel()

    def CreatePanel(self):

        #参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_prb_c = self.param_config.get("Gateway_station", "s_prb_c")
        except: s_prb_c = '1.4'

        try: s_id_sc = self.param_config.getint("Gateway_station", "s_id_sc")
        except: s_id_sc = 5

        try: s_modtype = self.param_config.get("Gateway_station", "s_modtype")
        except: s_modtype = 'QPSK'

        try: s_u_frequency = self.param_config.getint("Gateway_station", "s_u_frequency")
        except: s_u_frequency = 1985

        try: s_d_frequency = self.param_config.getint("Gateway_station", "s_d_frequency")
        except: s_d_frequency = 2185

        #链路带宽
        PRBList = ['1.4','3']
        prb_statictext = wx.StaticText(self, -1, u"链路带宽(MHz):")
        self.prb_c = wx.ComboBox(self, -1, s_prb_c, wx.DefaultPosition, wx.DefaultSize, PRBList, 0)

        #小区ID
        id_statictext = wx.StaticText(self, -1, u"小区ID:")
        self.id_sc = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.id_sc.SetRange(0,503)
        self.id_sc.SetValue(s_id_sc)

        #调制方式
        ModtypeList = ['QPSK','16QAM']
        modtype_st = wx.StaticText(self, -1, u"调制方式:")
        self.modtype = wx.ComboBox(self, -1, s_modtype, wx.DefaultPosition, wx.DefaultSize, ModtypeList, 0)

        #上行中心频率
        u_frequency_st = wx.StaticText(self, -1, u"上行中心频率:")
        self.u_frequency = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.u_frequency.SetRange(1980,2010)
        self.u_frequency.SetValue(s_u_frequency)

        #下行中心频率
        d_frequency_st = wx.StaticText(self, -1, u"下行中心频率:")
        self.d_frequency = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.d_frequency.SetRange(2170,2200)
        self.d_frequency.SetValue(s_d_frequency)

        #高级按钮
        self.senior_button = wx.Button(self, -1, u"高级")
        self.senior_button.SetBackgroundColour('black')
        self.senior_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Senior,self.senior_button)

        #######开始布局############
        #参数窗口
        sizer2 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer2.AddGrowableCol(1)
        sizer2.Add(prb_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.prb_c, 0, wx.EXPAND)
        sizer2.Add(modtype_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.modtype, 0, wx.EXPAND)
        sizer2.Add(id_statictext, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.id_sc, 0, wx.EXPAND)
        sizer2.Add(u_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.u_frequency, 0, wx.EXPAND)
        sizer2.Add(d_frequency_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.d_frequency, 0, wx.EXPAND)

        #高级按钮
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add((20,20), 1)
        sizer3.Add(self.senior_button, 0, wx.ALIGN_RIGHT)

        #添加参数子块，带边框的模块布局，包含参数和高级按钮
        sizer1 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'重要参数'), wx.VERTICAL)
        sizer1.Add(sizer2, 0, wx.EXPAND | wx.ALL, 15)
        # sizer1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        #box1垂直布局,box1即左半界面
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)
        box1.Add(sizer3, 0, wx.EXPAND | wx.ALL, 5)

        #自动调整界面尺寸
        self.SetSizer(box1)
        box1.Fit(self)
        box1.SetSizeHints(self)

    def Senior(self,event):
        # self.seniordialog = SeniorDialog_Gateway(None)
        self.seniordialog = SeniorDialog_Gateway(None)
        self.seniordialog.ok_button.Bind(wx.EVT_BUTTON, self.OnOk)
        # self.seniordialog.ShowModal()
        self.seniordialog.Show()

    def OnOk(self,event):
        #将设置好的参数写入配置文件
        self.param_config.read("param.conf")

        if "Gateway_station" not in self.param_config.sections():
            self.param_config.add_section("Gateway_station")

        self.param_config.set("Gateway_station", "s_data_rules", self.seniordialog.data_rules.GetValue())
        self.param_config.set("Gateway_station", "s_iter_num", self.seniordialog.iter_num.GetValue())
        self.param_config.set("Gateway_station", "s_delta_ss", self.seniordialog.Delta_ss.GetValue())
        self.param_config.set("Gateway_station", "s_shift", self.seniordialog.shift.GetValue())
        self.param_config.set("Gateway_station", "s_DMRS2", self.seniordialog.DMRS2.GetValue())
        self.param_config.set("Gateway_station", "s_decision_type", self.seniordialog.decision_type.GetValue())
        self.param_config.set("Gateway_station", "s_algorithm_c", self.seniordialog.algorithm_c.GetValue())
        self.param_config.set("Gateway_station", "s_gain_r_sc", self.seniordialog.Gain_r_sc.GetValue())
        self.param_config.set("Gateway_station", "s_gain_s_sc", self.seniordialog.Gain_s_sc.GetValue())
        self.param_config.set("Gateway_station", "s_exp_code_rate_u_sc", self.seniordialog.exp_code_rate_u.GetValue())
        self.param_config.set("Gateway_station", "s_exp_code_rate_d_sc", self.seniordialog.exp_code_rate_d.GetValue())
        self.param_config.set("Gateway_station", "s_samp_rate_sc", self.seniordialog.samp_rate_c.GetValue())
        self.param_config.set("Gateway_station", "s_t_reordering", self.seniordialog.t_Reordering.GetValue())
        self.param_config.set("Gateway_station", "s_t_statusprohibit", self.seniordialog.t_StatusProhibit.GetValue())
        self.param_config.set("Gateway_station", "s_t_pollretransmit", self.seniordialog.t_PollRetransmit.GetValue())
        self.param_config.set("Gateway_station", "s_maxretxthreshold", self.seniordialog.maxRetxThreshold.GetValue())
        self.param_config.set("Gateway_station", "s_sn_fieldlength", self.seniordialog.SN_FieldLength.GetValue())
        self.param_config.set("Gateway_station", "s_pollpdu", self.seniordialog.pollPDU.GetValue())
        self.param_config.set("Gateway_station", "s_pollbyte", self.seniordialog.pollByte.GetValue())
        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        self.seniordialog.Destroy()

class SeniorDialog_Gateway(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, title=u'信关站高级配置')
        self.parent = parent
        # self.SetTitle(u'信关站高级配置')
        self.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        self.param_config.read("param.conf")

        #创建面板
        self.SeniorPanel()

    def SeniorPanel(self):
        #参数从配置文件读取，如果配置文件不存在，则使用默认值
        try: s_data_rules = self.param_config.get("Gateway_station", "s_data_rules")
        except: s_data_rules = '规则递增'

        try: s_iter_num = self.param_config.getint("Gateway_station", "s_iter_num")
        except: s_iter_num = 4

        try: s_Delta_ss = self.param_config.getint("Gateway_station", "s_delta_ss")
        except: s_Delta_ss = 10

        try: s_shift = self.param_config.getint("Gateway_station", "s_shift")
        except: s_shift = 1

        try: s_DMRS2 = self.param_config.getint("Gateway_station", "s_DMRS2")
        except: s_DMRS2 = 4

        try: s_decision_type = self.param_config.get("Gateway_station", "s_decision_type")
        except: s_decision_type = 'soft'

        try: s_algorithm_c = self.param_config.get("Gateway_station", "s_algorithm_c")
        except: s_algorithm_c = 'Max_Log'

        try: s_gain_r_sc = self.param_config.getint("Gateway_station", "s_gain_r_sc")
        except: s_gain_r_sc = 10

        try: s_gain_s_sc = self.param_config.getint("Gateway_station", "s_gain_s_sc")
        except: s_gain_s_sc = 10

        try: s_exp_code_rate_u_sc = self.param_config.get("Gateway_station", "s_exp_code_rate_u_sc")
        except: s_exp_code_rate_u_sc = '0.45'

        try: s_exp_code_rate_d_sc = self.param_config.get("Gateway_station", "s_exp_code_rate_d_sc")
        except: s_exp_code_rate_d_sc = '0.45'

        try: s_samp_rate_sc = self.param_config.get("Gateway_station", "s_samp_rate_sc")
        except: s_samp_rate_sc = '2M'

        try: s_t_reordering = self.param_config.getint("Gateway_station", "s_t_reordering")
        except: s_t_reordering = 40

        try: s_t_statusprohibit = self.param_config.getint("Gateway_station", "s_t_statusprohibit")
        except: s_t_statusprohibit = 40

        try: s_t_pollretransmit = self.param_config.getint("Gateway_station", "s_t_pollretransmit")
        except: s_t_pollretransmit = 40

        try: s_maxretxthreshold = self.param_config.get("Gateway_station", "s_maxretxthreshold")
        except: s_maxretxthreshold = '4'

        try: s_sn_fieldlength = self.param_config.get("Gateway_station", "s_sn_fieldlength")
        except: s_sn_fieldlength = '10'

        try: s_pollpdu = self.param_config.get("Gateway_station", "s_pollpdu")
        except: s_pollpdu = '16'

        try: s_pollbyte = self.param_config.get("Gateway_station", "s_pollbyte")
        except: s_pollbyte = '125'

        #测试数据生成规则
        data_rules_list = [u'规则递增', u'指定种子的随机序列']
        data_rules_st = wx.StaticText(self, -1, u"测试数据生成规则:")
        self.data_rules = wx.ComboBox(self, -1, s_data_rules, wx.DefaultPosition, wx.DefaultSize, data_rules_list, 0)

        #译码算法迭代次数
        iter_num_st = wx.StaticText(self, -1, u"译码算法迭代次数:")
        self.iter_num = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.iter_num.SetRange(1,8)
        self.iter_num.SetValue(s_iter_num)

        #用于配置fss
        Delta_ss_st = wx.StaticText(self, -1, u"Δss:")
        self.Delta_ss = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.Delta_ss.SetRange(0,29)
        self.Delta_ss.SetValue(s_Delta_ss)

        #循环移位间隔
        shift_st = wx.StaticText(self, -1, u"循环移位间隔:")
        self.shift = wx.SpinCtrl(self, -1, "", (-1,-1))
        self.shift.SetRange(1,3)
        self.shift.SetValue(s_shift)

        #解调参考符号DMRS2
        DMRS2_st = wx.StaticText(self, -1, "DMRS2:")
        self.DMRS2 = wx.SpinCtrl(self, -1, "", (-1,-1))
        self.DMRS2.SetRange(0,7)
        self.DMRS2.SetValue(s_DMRS2)

        #判决方式
        decision_type_list = ['soft', 'hard']
        decision_type_st = wx.StaticText(self, -1, u"判决方式:")
        self.decision_type = wx.ComboBox(self, -1, s_decision_type, wx.DefaultPosition, wx.DefaultSize, decision_type_list, 0)

        #Turbo译码算法 
        algorithm_list = ['Max_Log',u'维特比']
        algorithm_st = wx.StaticText(self, -1 ,u"Turbo译码算法:")
        self.algorithm_c = wx.ComboBox(self, -1, s_algorithm_c, wx.DefaultPosition, wx.DefaultSize, algorithm_list, 0)

        #收发增益控制
        Gain_r_st = wx.StaticText(self, -1 ,u"接收增益(dB):")
        self.Gain_r_sc = wx.SpinCtrl(self, -1, "", (-1, -1))
        self.Gain_r_sc.SetRange(0,30)
        self.Gain_r_sc.SetValue(s_gain_r_sc)

        Gain_s_st = wx.StaticText(self, -1, u"发送增益(dB):")
        self.Gain_s_sc = wx.SpinCtrl(self,-1, "",(-1, -1))
        self.Gain_s_sc.SetRange(0,20)
        self.Gain_s_sc.SetValue(s_gain_s_sc)

        #上行编码码率
        exp_code_rate_u_st = wx.StaticText(self, -1, u"上行编码码率:")
        self.exp_code_rate_u = wx.TextCtrl(self, -1, s_exp_code_rate_u_sc)

        #下行编码码率
        exp_code_rate_d_st = wx.StaticText(self, -1, u"下行编码码率:")
        self.exp_code_rate_d = wx.TextCtrl(self, -1, s_exp_code_rate_d_sc)

        #采样率
        samp_rate_list = ['2M','4M']
        samp_rate_st = wx.StaticText(self, -1 ,u"采样率:")
        self.samp_rate_c = wx.ComboBox(self, -1, s_samp_rate_sc, wx.DefaultPosition, wx.DefaultSize, samp_rate_list, 0)

        #由RLC UM的收端或AM使用，定时超时表明目前接收到但尚未递交高层的一段数据必须丢弃
        t_Reordering_st = wx.StaticText(self, -1, "t_Reordering(ms):")
        self.t_Reordering = wx.Slider(self, -1, s_t_reordering, 0, 200, size=(300, -1),
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        #设置滑块的刻度
        self.t_Reordering.SetTickFreq(5, 1)  
        #设置箭头调整的幅度
        self.t_Reordering.SetLineSize(10)
        #调整pageup/pagedown调整的幅度
        self.t_Reordering.SetPageSize(5)

        #由RLC AM使用，发送完一个状态报告之后，禁止再次发送的时间范围
        t_StatusProhibit_st = wx.StaticText(self, -1, "t_StatusProhibit(ms):")
        self.t_StatusProhibit = wx.Slider(self, -1, s_t_statusprohibit, 0, 500, 
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.t_StatusProhibit.SetTickFreq(10, 1) 
        self.t_StatusProhibit.SetLineSize(10)
        self.t_StatusProhibit.SetPageSize(5)

        #由RLC AM使用，发起状态查询，即主动请求对端发送状态报告的周期
        t_PollRetransmit_st = wx.StaticText(self, -1, "t_PollRetransmit(ms):")
        self.t_PollRetransmit = wx.Slider(self, -1, s_t_pollretransmit, 5, 500, 
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS )
        self.t_PollRetransmit.SetTickFreq(10, 1) 
        self.t_PollRetransmit.SetLineSize(10)
        self.t_PollRetransmit.SetPageSize(5)

        #最大重传次数
        maxRetxThreshold_list = ['1', '2', '3', '4', '6', '8', '16', '32']
        maxRetxThreshold_st = wx.StaticText(self, -1, u"最大重传次数:")
        self.maxRetxThreshold = wx.ComboBox(self, -1, s_maxretxthreshold, wx.DefaultPosition, wx.DefaultSize, maxRetxThreshold_list, 0)

        #RLC UM使用，PDU中序号占用的比特数
        SN_FieldLength_list = ['5','10']
        SN_FieldLength_st = wx.StaticText(self, -1, "SN_FieldLength:")
        self.SN_FieldLength = wx.ComboBox(self, -1, s_sn_fieldlength, wx.DefaultPosition, wx.DefaultSize, SN_FieldLength_list, 0)

        #RLC AM使用，当发送的PDU个数大于该计数器，强制启动状态查询
        pollPDU_list = ['4', '8', '16', '32', '64', '128', '256']
        pollPDU_st = wx.StaticText(self, -1, "pollPDU:")
        self.pollPDU = wx.ComboBox(self, -1, s_pollpdu, wx.DefaultPosition, wx.DefaultSize, pollPDU_list, 0)

        #RLC AM使用，当发送的SDU字节数大于该计数器，强制启动状态查询
        pollByte_list = ['25','50','75','100','125','250','375','500','750','1000','1250','1500','2000','3000']
        pollByte_st = wx.StaticText(self, -1, "pollByte(KB):")
        self.pollByte = wx.ComboBox(self, -1, s_pollbyte, wx.DefaultPosition, wx.DefaultSize, pollByte_list, 0)

        #确定设置按钮
        self.ok_button = wx.Button(self, -1, u"确定")
        self.ok_button.SetBackgroundColour('black')
        self.ok_button.SetForegroundColour('white')
        # self.ok_button.SetDefault()

        #帮助按钮
        self.help_button = wx.Button(self, -1, u"帮助")
        self.help_button.SetBackgroundColour('black')
        self.help_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.Help,self.help_button)

        #MAC/PHY布局
        sizer2 = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        sizer2.AddGrowableCol(1)
        sizer2.Add(data_rules_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.data_rules, 0, wx.EXPAND)
        sizer2.Add(iter_num_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.iter_num, 0, wx.EXPAND)
        sizer2.Add(Delta_ss_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Delta_ss, 0, wx.EXPAND)
        sizer2.Add(shift_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.shift, 0, wx.EXPAND)
        sizer2.Add(DMRS2_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.DMRS2, 0, wx.EXPAND)
        sizer2.Add(decision_type_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.decision_type, 0, wx.EXPAND)
        sizer2.Add(algorithm_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.algorithm_c, 0, wx.EXPAND)
        sizer2.Add(Gain_r_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_r_sc, 0, wx.EXPAND)
        sizer2.Add(Gain_s_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.Gain_s_sc, 0, wx.EXPAND)
        sizer2.Add(exp_code_rate_u_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.exp_code_rate_u, 0, wx.EXPAND)
        sizer2.Add(exp_code_rate_d_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.exp_code_rate_d, 0, wx.EXPAND)
        sizer2.Add(samp_rate_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.samp_rate_c, 0, wx.EXPAND)

        #RLC布局
        sizer4 = wx.FlexGridSizer(cols=2,hgap=5,vgap=12)
        sizer4.AddGrowableCol(1)
        sizer4.Add(t_Reordering_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_Reordering, 0, wx.EXPAND)
        sizer4.Add(t_StatusProhibit_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_StatusProhibit, 0, wx.EXPAND)
        sizer4.Add(t_PollRetransmit_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.t_PollRetransmit, 0, wx.EXPAND)
        sizer4.Add(maxRetxThreshold_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.maxRetxThreshold, 0, wx.EXPAND)
        sizer4.Add(SN_FieldLength_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.SN_FieldLength, 0, wx.EXPAND)
        sizer4.Add(pollPDU_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.pollPDU, 0, wx.EXPAND)
        sizer4.Add(pollByte_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer4.Add(self.pollByte, 0, wx.EXPAND)

        #确定按钮布局
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add((20,20), 1)
        sizer3.Add(self.ok_button, 0, wx.ALIGN_RIGHT)
        sizer3.Add(self.help_button, 0, wx.ALIGN_RIGHT)

        #添加参数子块，带边框的模块布局
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'MAC/PHY层参数'), wx.VERTICAL)
        sizer5.Add(sizer2, 0, wx.EXPAND | wx.ALL, 10)

        sizer6 = wx.StaticBoxSizer(wx.StaticBox(self, wx.NewId(), u'RLC层参数'), wx.VERTICAL)
        sizer6.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(sizer5, 0, wx.EXPAND | wx.ALL, 10)
        sizer1.Add(sizer6, 0, wx.EXPAND | wx.ALL, 10)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)
        box.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        #自动调整界面尺寸
        self.SetSizer(box)
        box.Fit(self)
        box.SetSizeHints(self)

    def Help(self,event):
        self.dialog = Help_Dialog(self)
        # self.dialog.ShowModal()
        self.dialog.Show()

class Help_Dialog(wx.Frame):

    def __init__(self,parent):
        wx.Frame.__init__(self, None, title="配置项目表",
                          size=(1400,800))

        self.parent = parent

        grid = wx.grid.Grid(self)
        grid.CreateGrid(45,10)

        attr1 = wx.grid.GridCellAttr()
        attr1.SetReadOnly(True)
        # attr1.SetBackgroundColour("white")

        for row in range(4):
            grid.SetColAttr(row+1, attr1)

        attr2 = wx.grid.GridCellAttr()
        attr2.SetReadOnly(True)
        attr2.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        grid.SetColAttr(0, attr2)
        grid.SetColAttr(5, attr2)

        grid.SetCellSize(0, 0, 7, 1)
        grid.SetCellSize(0, 5, 7, 1)
        grid.SetCellSize(7, 0, 33, 1)
        grid.SetCellSize(7, 5, 33, 1)

        grid.SetCellValue(0, 0, "\n\n\n\n\n     RLC")  
        grid.SetCellValue(0, 5, "\n\n\n\n\n\tTS36.331 \n\t6.3.2小节\n\tRLC-Config")    
        grid.SetCellValue(7, 0, "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nMAC/PHY")    
        grid.SetCellValue(7, 5, "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\tTS36.211\n\n\tTS36.321")  

        grid.SetColSize(1, 150)
        grid.SetColSize(2, 300)
        grid.SetColSize(4, 300)
        grid.SetColSize(5, 150)

        list1 = ['t-Reordering','t-StatusProhibit','t-PollRetransmit','maxRetxThreshold','SN-FieldLength','pollPDU',
        'pollByte','u_frequency','d_frequency','prb','id_cell','mod_type','RNTI','data_rules','t_advance ','iter_num',
        'n_pucch','shift','K_TC','DMRS1','DMRS2','decision_type','Turbo译码算法','Gain_s','Gain_r','exp_code_rate_u',
        'exp_code_rate_d','samp_rate','m','M','Threshold','Delta_ss(Δss)','SRS_period','SRS_offset','SR_periodicity',
        'SR_offset','C_SRS','B_SRS','n_SRS','n_RRC']
        list2 = ['由RLC UM的收端或AM使用，定时超时表明\n目前接收到但尚未递交高层的一段数据必须\n丢弃','由RLC AM使用，发送完一个状态报告之后，\n禁止再次发送的时间范围',
        '由RLC AM使用，发起状态查询，即主动请求\n对端发送状态报告的周期','最大重传次数','RLC UM使用，PDU中序号占用的比特数',
        'RLC AM使用，当发送的PDU个数大于该计\n数器，强制启动状态查询','RLC AM使用，当发送的SDU字节数大于该计\n数器，强制启动状态查询',
        '上行中心频率','下行中心频率','链路带宽','小区ID','调制方式','终端RNTI','测试数据生成规则','时间提前量','译码算法迭代次数',
        '用户资源索引','循环移位间隔','两个终端分别配置','解调参考符号','解调参考符号','判决方式','Turbo译码算法，DL/UL各自单独设置',
        '发送增益控制','接收增益控制','上行编码码率','下行编码码率','采样率','m_part优化算法插零数','M_part算法分段数','阈值',
        '用于配置fss','SRS周期','SRS补偿','SR周期','SR补偿','由高层的srs-BandwidthConfig参数得到，终\n端用此参数确定序列的长度',
        '由高层的srs-Bandwidth参数得到，终端用此\n参数确定序列的长度','由高层cyclicshift参数得到，终端用此参数确\n定序列的循环移位',
        '由高层freqDomainPositon参数给出，终端用\n此参数确定映射时的频带起始位置']
        list3 = ['40ms','40ms','40ms','4','10','16','125KB','1985','2175','1.4MHz','5','QPSK','100','重复','0','4','0、18',
        '1','0、1','4','4','soft','Max-Log','10dB','10dB','0.45','0.45','2M','2','2','0.85','10','2','0','10','待定','4','1',
        '4','0']
        list4 = ['0ms~100ms,间隔5ms,110ms~200ms,\n间隔10ms离散可调','0ms~250ms,间隔5ms离散可调,\n300,350,400, 450,500',
        '5ms~250ms,间隔5ms离散可调,\n300,350,400, 450,500','1,2,3,4,6,8,16,32','5,10','4，8，16，32，64，128，256，\n无穷大（禁用）',
        '25KB,50,75,100,125,250,375,500,750,1000,\n1250,1500,2000,3000,无穷大（禁用）','1980-2010MHz','2170～2200MHz','1.4MHz、3MHz',
        '0~503','QPSK/16QAM','0x003D～0xFFF3','规则递增/指定种子的随机序列','待测','1~8','0~35','1,2,3','0、1','0,2,3,4,6,8,9,10',
        '0,1,2,3,4,5,6,7','hard/soft','Max-Log/维特比','0～20dB','0～30dB','0.3～0.6','0.3～0.6','2M 、4M','1,2,4','1,2,4,8',
        '0.75~0.95(待测)','0~29','1,2,5,10','0,1,2,3,4,5,6,8','5,10,20,40,80,2,1','0～SR_periodicity-1','0,1,2,3,4,5,6,7','0,1,2,3',
        '0,1,2,3,4,5,6,7','0~23']

        self.colLabels = ['层面','名称','含义','默认值','可选值','相关标准章节']

        for row in range(6):
            grid.SetColLabelValue(row, self.colLabels[row])

        for row in range(40):
            grid.SetCellValue(row, 1, list1[row])

        for row in range(40):
            grid.SetCellValue(row, 2, list2[row])

        for row in range(40):
            grid.SetCellValue(row, 3, list3[row])

        for row in range(40):
            grid.SetCellValue(row, 4, list4[row])

        num_list = [0,1,2,5,6,36,37,38,39]
        for num in num_list:
            grid.SetRowSize(num, 40)

class PanelOne(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.state = ['Red']
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.SetBrush(wx.Brush(self.state[0]))
        dc.DrawCircle(8, 8, 8)

    def state_green(self):
        self.state=['green']
        self.Refresh()
    def state_red(self):
        self.state=['red']
        self.Refresh()

class MainFrame(wx.Frame):
    def __init__(self,parent,id):
        wx.Frame.__init__(self, None, title=u"控制界面")
        self.Centre()
        self.panel = wx.Panel(self, -1)
        self.panel.SetBackgroundColour("white")

        self.param_config = ConfigParser.ConfigParser()
        
        #创建面板
        self.createframe()

        # 创建一个pubsub接收器,用于接收从子线程传递过来的消息
        Publisher().subscribe(self.updateDisplay, "update")
        Publisher().subscribe(self.updateDisplay_t, "update_t")

    def createframe(self):
        #绑定窗口的关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        #创建状态栏
        # self.panel.Bind(wx.EVT_MOTION, self.OnDataMotion)  
        self.statusbar = self.CreateStatusBar()  
        #将状态栏分割为2个区域,比例为1:1
        self.statusbar.SetFieldsCount(2)  
        self.statusbar.SetStatusWidths([-1, -1])

        #启动按钮
        self.start_button = wx.Button(self.panel, -1, u"启动")
        self.start_button.SetBackgroundColour((0, 0, 0, 255))
        self.start_button.SetForegroundColour(wx.WHITE)
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.start_button) 
        self.start_button.Disable()

        #停止按钮
        self.stop_button = wx.Button(self.panel, -1, u"停止")
        self.stop_button.SetBackgroundColour((0, 0, 0, 255))
        self.stop_button.SetForegroundColour(wx.WHITE)
        self.Bind(wx.EVT_BUTTON, self.OnStop, self.stop_button) 
        self.stop_button.Disable()

        #监听按钮
        self.monitor_button = wx.Button(self.panel, -1, u"监听")
        self.monitor_button.SetBackgroundColour('black')
        self.monitor_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON, self.OnMonitor, self.monitor_button)  
        # self.monitor_button.SetDefault() 

        #配置按钮
        self.config_button = wx.Button(self.panel, -1, u"配置")
        self.config_button.SetBackgroundColour('black')
        self.config_button.SetForegroundColour('white')
        self.Bind(wx.EVT_BUTTON,self.OnConfig,self.config_button)

        #设置IP地址和端口号
        self.param_config.read("param.conf")
        try: s_ip = self.param_config.get("address", "s_ip")
        except: s_ip = '192.168.139.180'

        try: s_port = self.param_config.get("address", "s_port")
        except: s_port = '7000'

        try: s_num = self.param_config.getint("work_mod", "s_num")
        except: s_num = 0

        ip_st = wx.StaticText(self.panel, -1, u"IP地址 :")  
        self.IPText = wx.TextCtrl(self.panel, -1, s_ip)  
        # self.IPText.SetBackgroundColour('#c2e6f8')
        # self.IPText.SetForegroundColour('black')
        port_st = wx.StaticText(self.panel, -1, u"端口号 :")  
        self.PortText = wx.TextCtrl(self.panel, -1, s_port)
        # self.PortText.SetBackgroundColour('#c2e6f8')
        # self.PortText.SetForegroundColour('black')

        # 在面板上创建一个notebook
        nb = wx.Notebook(self.panel)
        self.page1 = Gateway_station(nb)
        self.page2 = Terminal(nb)
        nb.AddPage(self.page1, u"信关站")
        nb.AddPage(self.page2, u"终端")

        #状态显示文本框
        gateway_st = wx.StaticText(self.panel, -1, "信关站:")  
        self.panel_gateway = PanelOne(self.panel)

        terminal_st_A = wx.StaticText(self.panel, -1, "终端A:")  
        self.panel_terminal_A = PanelOne(self.panel)

        terminal_st_B = wx.StaticText(self.panel, -1, "终端B:")  
        self.panel_terminal_B = PanelOne(self.panel)

        self.DisplayText = wx.TextCtrl(self.panel, -1, '',   
                size=(250, 460), style=wx.TE_MULTILINE | wx.TE_READONLY) 
        self.DisplayText.SetBackgroundColour('gray')

        #模式选择
        work_mod_list = ['数据测试演示', '音频业务演示', '视频业务演示']
        self.work_mod = wx.RadioBox(self.panel, -1, "业务模式", wx.DefaultPosition, wx.DefaultSize,
                        work_mod_list, 3, wx.RA_SPECIFY_COLS)
        self.work_mod.SetBackgroundColour((250,250,250,255))
        self.work_mod.SetSelection(s_num)

        #启动、停止、监听、配置按钮水平布局
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.monitor_button)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.config_button)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.start_button)
        sizer1.Add((20,20), 1)
        sizer1.Add(self.stop_button)
        sizer1.Add((20,20), 1)

        sizer2 = wx.FlexGridSizer(cols=4, hgap=10, vgap=10)
        sizer2.AddGrowableCol(1)
        sizer2.Add(ip_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.IPText, 0, wx.EXPAND)
        sizer2.Add(port_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer2.Add(self.PortText, 0, wx.EXPAND)

        sizer3 = wx.FlexGridSizer(cols=6, hgap=10, vgap=10)
        sizer3.AddGrowableCol(1)
        sizer3.AddGrowableCol(3)
        sizer3.Add(gateway_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.panel_gateway, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(terminal_st_A, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.panel_terminal_A, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(terminal_st_B, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.panel_terminal_B, 1, wx.ALIGN_CENTER_VERTICAL)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(nb, 0, wx.EXPAND | wx.ALL, 10)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL, 10)
        box1.Add(self.work_mod,0,wx.EXPAND | wx.ALL, 10)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,10)
        box1.Add(sizer1,0,wx.EXPAND | wx.ALL, 10)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)

        box2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'状态显示'), wx.VERTICAL)
        box2.Add(self.DisplayText, 0, wx.EXPAND | wx.ALL, 10)
        box2.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(box1, 0, wx.EXPAND | wx.ALL, 20)
        box.Add(box2, 1, wx.EXPAND | wx.ALL, 20)

        #自动调整界面尺寸
        self.panel.SetSizer(box)
        box.Fit(self)
        box.SetSizeHints(self)

    # def OnDataMotion(self, event):  
          
    #     #设置状态栏1内容  
    #     # self.statusbar.SetStatusText(u"鼠标位置：" + str(event.GetPositionTuple()), 0)
    #     # self.statusbar.SetStatusText(u"误码率：" + str(), 0)  
    #     self.statusbar.SetStatusText(u"误码率：", 0)  
          
    #     #设置状态栏2内容
    #     self.statusbar.SetStatusText(u"误帧率：", 1)  
          
    #     #设置状态栏3内容  
    #     self.statusbar.SetStatusText(u"信息速率：", 2)  
               
    #     event.Skip() 

    def updateDisplay(self, msg): 
        """
        从线程接收数据并且在界面更新显示
        """
        self.DisplayText.AppendText(msg.data)

    def updateDisplay_t(self, msg): 
        """
        从线程接收数据并且在界面更新显示
        """
        self.status = msg.data
        
        # if len(self.clients)==2:
        #     self.panel_terminal_A.state_green()
        #     self.panel_terminal_B.state_green()
        # elif len(self.clients)==1:
        #     self.panel_terminal_A.state_green()
        #     self.panel_terminal_B.state_red()
        # elif len(self.clients)==0:
        #     self.panel_terminal_A.state_red()
        #     self.panel_terminal_B.state_red()

        if self.status.has_key('A_ip'):
            self.panel_terminal_A.state_green()
        else:
            self.panel_terminal_A.state_red()

        if self.status.has_key('B_ip'):
            self.panel_terminal_B.state_green()
        else:
            self.panel_terminal_B.state_red()

        if self.status.has_key('gateway'):
            if self.status['gateway'] =='true':
                self.panel_gateway.state_green()
            else:
                self.panel_gateway.state_red()

        if self.work_mod.GetSelection()==0:
            try:
                self.statusbar.SetStatusText(u"误码率："+str(self.status['get_ber']), 0)
                self.statusbar.SetStatusText(u"误帧率："+str(self.status['get_fer']), 1)
            except:
                pass
        else:
            self.statusbar.SetStatusText(u"误码率：", 0)
            self.statusbar.SetStatusText(u"误帧率：", 1)

    def OnStart(self,event):
        ###############page1#################
        self.page1.prb_c.Disable()
        self.page1.modtype.Disable()
        self.page1.id_sc.Disable()
        self.page1.u_frequency.Disable()
        self.page1.d_frequency.Disable()
        ###############page2#################
        self.page2.u_frequency.Disable()
        self.page2.d_frequency.Disable()
        self.page2.m_part.Disable()
        self.page2.M_part.Disable()
        self.page2.Threshold.Disable()
        #############work_mod################
        self.work_mod.Disable()
        try:
            self.start_button.Disable()
            self.stop_button.Enable()
            for s in self.inputs:
                if s is self.server:
                    pass
                else:
                    s.send('start_block')
                    self.DisplayText.AppendText(u'启动...\n')
        except:
            print "请先建立连接"
            self.DisplayText.AppendText(u'请先建立连接...\n')

    def OnStop(self,event):
        ###############page1#################
        self.page1.prb_c.Enable()
        self.page1.modtype.Enable()
        self.page1.id_sc.Enable()
        self.page1.u_frequency.Enable()
        self.page1.d_frequency.Enable()
        ###############page2#################
        self.page2.u_frequency.Enable()
        self.page2.d_frequency.Enable()
        self.page2.m_part.Enable()
        self.page2.M_part.Enable()
        self.page2.Threshold.Enable()
        #############work_mod################
        self.work_mod.Enable()
        try:
            self.stop_button.Disable()
            self.start_button.Enable()
            for s in self.inputs:
                if s is self.server:
                    pass
                else:
                    s.send('stop_block')
                    self.DisplayText.AppendText(u'停止...\n')
        except:
            print "请先建立连接"
            self.DisplayText.AppendText(u'请先建立连接...\n')

    def OnConfig(self,event):
        self.start_button.Enable()
        self.stop_button.Enable()
        self.param_config.read("param.conf")
        if "work_mod" not in self.param_config.sections():
            self.param_config.add_section("work_mod")

        #work_mod
        self.param_config.set("work_mod", "s_num", self.work_mod.GetSelection())

        if "Gateway_station" not in self.param_config.sections():
            self.param_config.add_section("Gateway_station")

        #Gateway_station
        self.param_config.set("Gateway_station", "s_prb_c", self.page1.prb_c.GetValue())
        self.param_config.set("Gateway_station", "s_id_sc", self.page1.id_sc.GetValue())
        self.param_config.set("Gateway_station", "s_modtype", self.page1.modtype.GetValue())
        self.param_config.set("Gateway_station", "s_u_frequency", self.page1.u_frequency.GetValue())
        self.param_config.set("Gateway_station", "s_d_frequency", self.page1.d_frequency.GetValue())

        if "Terminal" not in self.param_config.sections():
            self.param_config.add_section("Terminal")

        #Terminal
        self.param_config.set("Terminal", "s_u_frequency", self.page2.u_frequency.GetValue())
        self.param_config.set("Terminal", "s_d_frequency", self.page2.d_frequency.GetValue())
        self.param_config.set("Terminal", "s_m_part", self.page2.m_part.GetValue())
        self.param_config.set("Terminal", "s_bigm_part", self.page2.M_part.GetValue())
        self.param_config.set("Terminal", "s_threshold", self.page2.Threshold.GetValue())
        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        #高级界面参数，如果存在param.conf文件，读取，否则等于param{}里的初始值
        try:
            self.param_config.read("param.conf")
        except:
            param = {'RNTI_A':'100', 'RNTI_B':'200', 't_advance_A':'0', 't_advance_B':'0',
                'n_pucch_A':'0','n_pucch_B':'18','data_rules_T':'规则递增','iter_num_T':'4', 
                'Delta_ss_T':'10', 'shift_T':'1', 'DMRS1_T':'4', 'decision_type_T':'soft', 'algorithm_T':'Max_Log',
                'gain_r_T':'10', 'gain_s_T':'10', 'samp_rate_T':'2M', 'C_SRS_A':'4', 'B_SRS_A':'1', 'n_SRS_A':'4', 
                'n_RRC_A':'0', 'C_SRS_B':'5', 'B_SRS_B':'2', 'n_SRS_B':'5', 'n_RRC_B':'0','K_TC_A':'0','K_TC_B':'1',
                'SRS_period_A':'2','SRS_period_B':'2','SRS_offset_A':'0','SRS_offset_B':'1','SR_periodicity_A':'10',
                'SR_periodicity_B':'10','SR_offset_A':'2','SR_offset_B':'4','t_Reordering_T':'40', 
                't_StatusProhibit_T':'40','t_PollRetransmit_T':'40','maxRetxThreshold_T':'4', 'SN_FieldLength_T':'10',
                'pollPDU_T':'16','pollByte_T':'125','data_rules_G':'规则递增','iter_num_G':'4', 'Delta_ss_G':'10', 
                'shift_G':'1', 'DMRS2_G':'4','decision_type_G':'soft', 'algorithm_G':'Max_Log', 'gain_r_G':'10',
                'gain_s_G':'10', 'samp_rate_G':'2M', 'exp_code_rate_u_G':'0.45', 'exp_code_rate_d_G':'0.45',
                't_Reordering_G':'40', 't_StatusProhibit_G':'40','t_PollRetransmit_G':'40', 'maxRetxThreshold_G':'4', 
                'SN_FieldLength_G':'10', 'pollPDU_G':'16', 'pollByte_G':'125'}
        else:
            #Terminal
            global param
            param['RNTI_A'] = self.param_config.get("Terminal", "s_rnti_a")
            param['RNTI_B'] = self.param_config.get("Terminal", "s_rnti_b")
            param['t_advance_A'] = self.param_config.get("Terminal", "s_t_advance_a")
            param['t_advance_B'] = self.param_config.get("Terminal", "s_t_advance_b")
            param['n_pucch_A'] = self.param_config.get("Terminal", "s_n_pucch_a")
            param['n_pucch_B'] = self.param_config.get("Terminal", "s_n_pucch_b")
            param['data_rules_T'] = self.param_config.get("Terminal", "s_data_rules")
            param['iter_num_T'] = self.param_config.get("Terminal", "s_iter_num")
            param['Delta_ss_T'] = self.param_config.get("Terminal", "s_delta_ss")
            param['shift_T'] = self.param_config.get("Terminal", "s_shift")
            param['DMRS1_T'] = self.param_config.get("Terminal", "s_DMRS1")
            param['decision_type_T'] = self.param_config.get("Terminal", "s_decision_type")
            param['algorithm_T'] = self.param_config.get("Terminal", "s_algorithm_c")
            param['gain_r_T'] = self.param_config.get("Terminal", "s_gain_r_sc")
            param['gain_s_T'] = self.param_config.get("Terminal", "s_gain_s_sc")
            param['samp_rate_T'] = self.param_config.get("Terminal", "s_samp_rate_sc")
            param['C_SRS_A'] = self.param_config.get("Terminal", "s_c_srs_a")
            param['B_SRS_A'] = self.param_config.get("Terminal", "s_b_srs_a")
            param['n_SRS_A'] = self.param_config.get("Terminal", "s_n_srs_a")
            param['n_RRC_A'] = self.param_config.get("Terminal", "s_n_rrc_a")
            param['C_SRS_B'] = self.param_config.get("Terminal", "s_c_srs_b")
            param['B_SRS_B'] = self.param_config.get("Terminal", "s_b_srs_b")
            param['n_SRS_B'] = self.param_config.get("Terminal", "s_n_srs_b")
            param['n_RRC_B'] = self.param_config.get("Terminal", "s_n_rrc_b")
            param['K_TC_A'] = self.param_config.get("Terminal", "s_k_tc_a")
            param['K_TC_B'] = self.param_config.get("Terminal", "s_k_tc_b")
            param['SRS_period_A'] = self.param_config.get("Terminal", "s_srs_period_a")
            param['SRS_period_B'] = self.param_config.get("Terminal", "s_srs_period_b")
            param['SRS_offset_A'] = self.param_config.get("Terminal", "s_srs_offset_a")
            param['SRS_offset_B'] = self.param_config.get("Terminal", "s_srs_offset_b")
            param['SR_periodicity_A'] = self.param_config.get("Terminal", "s_sr_periodicity_a")
            param['SR_periodicity_B'] = self.param_config.get("Terminal", "s_sr_periodicity_b")
            param['SR_offset_A'] = self.param_config.get("Terminal", "s_sr_offset_a")
            param['SR_offset_B'] = self.param_config.get("Terminal", "s_sr_offset_b")
            param['t_Reordering_T'] = self.param_config.get("Terminal", "s_t_reordering")
            param['t_StatusProhibit_T'] = self.param_config.get("Terminal", "s_t_statusprohibit")
            param['t_PollRetransmit_T'] = self.param_config.get("Terminal", "s_t_pollretransmit")
            param['maxRetxThreshold_T'] = self.param_config.get("Terminal", "s_maxretxthreshold")
            param['SN_FieldLength_T'] = self.param_config.get("Terminal", "s_sn_fieldlength")
            param['pollPDU_T'] = self.param_config.get("Terminal", "s_pollpdu")
            param['pollByte_T'] = self.param_config.get("Terminal", "s_pollbyte")
            #Gateway_station  
            param['data_rules_G'] = self.param_config.get("Gateway_station", "s_data_rules")
            param['iter_num_G'] = self.param_config.get("Gateway_station", "s_iter_num")
            param['Delta_ss_G'] = self.param_config.get("Gateway_station", "s_delta_ss")
            param['shift_G'] = self.param_config.get("Gateway_station", "s_shift")
            param['DMRS2_G'] = self.param_config.get("Gateway_station", "s_DMRS2")
            param['decision_type_G'] = self.param_config.get("Gateway_station", "s_decision_type")
            param['algorithm_G'] = self.param_config.get("Gateway_station", "s_algorithm_c")
            param['gain_r_G'] = self.param_config.get("Gateway_station", "s_gain_r_sc")
            param['gain_s_G'] = self.param_config.get("Gateway_station", "s_gain_s_sc")
            param['exp_code_rate_u_G'] = self.param_config.get("Gateway_station", "s_exp_code_rate_u_sc")
            param['exp_code_rate_d_G'] = self.param_config.get("Gateway_station", "s_exp_code_rate_d_sc")
            param['samp_rate_G'] = self.param_config.get("Gateway_station", "s_samp_rate_sc")
            param['t_Reordering_G'] = self.param_config.get("Gateway_station", "s_t_reordering")
            param['t_StatusProhibit_G'] = self.param_config.get("Gateway_station", "s_t_statusprohibit")
            param['t_PollRetransmit_G'] = self.param_config.get("Gateway_station", "s_t_pollretransmit")
            param['maxRetxThreshold_G'] = self.param_config.get("Gateway_station", "s_maxretxthreshold")
            param['SN_FieldLength_G'] = self.param_config.get("Gateway_station", "s_sn_fieldlength")
            param['pollPDU_G'] = self.param_config.get("Gateway_station", "s_pollpdu")
            param['pollByte_G'] = self.param_config.get("Gateway_station", "s_pollbyte")

        #主界面的参数
        param['work_mod'] = self.work_mod.GetItemLabel(self.work_mod.GetSelection())
        param['Bandwidth'] = self.page1.prb_c.GetValue()
        param['id_cell'] = self.page1.id_sc.GetValue()
        param['mod_type'] = self.page1.modtype.GetValue()
        param['u_frequency_G'] = self.page1.u_frequency.GetValue()
        param['d_frequency_G'] = self.page1.d_frequency.GetValue()

        param['u_frequency_T'] = self.page2.u_frequency.GetValue()
        param['d_frequency_T'] = self.page2.d_frequency.GetValue()
        param['m_part'] = self.page2.m_part.GetValue()
        param['M_part'] = self.page2.M_part.GetValue()
        param['Threshold'] = self.page2.Threshold.GetValue()
        print param
        jparam = json.dumps(param) 
        self.send_param = jparam

        try:
            for s in self.inputs:
                if s is self.server:
                    pass
                else:
                    s.send(self.send_param)
        except:
            print "请先建立连接"
            self.DisplayText.AppendText(u'请先建立连接...\n')

    def OnMonitor(self,event):
        self.param_config.read("param.conf")
        if "address" not in self.param_config.sections():
            self.param_config.add_section("address")

        #address
        self.param_config.set("address", "s_ip", self.IPText.GetValue())
        self.param_config.set("address", "s_port", self.PortText.GetValue())

        #写入配置文件
        param_file = open("param.conf","w")
        self.param_config.write(param_file)
        param_file.close()

        #监视按钮按下之后，按钮不能再次按下
        self.monitor_button.Disable()
        self.IPText.Disable()
        self.PortText.Disable()

        t1 = threading.Thread(target = self.start_server)
        t1.setDaemon(True)
        t1.start()

    def start_server(self): 
        try:
            #创建socket并绑定  
            self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
            self.port = int(self.PortText.GetValue())  
            self.host = str(self.IPText.GetValue())  
            self.server.setblocking(False)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
            self.server.bind((self.host, self.port))  
            self.server.listen(3)  
            wx.CallAfter(Publisher().sendMessage, "update", u'控制界面等待连接...\n')
        except:
            self.monitor_button.Enable()
            self.IPText.Enable()
            self.PortText.Enable()
    
        # 读socket
        self.inputs = [ self.server ] 

        # 写socket
        outputs = []  

        #客户端地址
        self.clients = {}
  
        # 消息队列
        message_queues = {} 
  
        while self.inputs:  
            # 等待出现至少一个连接准备好,要求处理
            print "等待事件"  
            readable, writable, exceptional = select.select(self.inputs, outputs, self.inputs)  
              
            # 读socket处理
            for s in readable:  
                # 如果读socket是server，则建立连接；如果读socket是connection，则接收数据
                if s is self.server:  
                    try:
                        self.connection, self.client_address = s.accept()  
                    except:
                        print '请输入正确的IP地址'
                        sys.exit()
                    else:
                        wx.CallAfter(Publisher().sendMessage, "update", u'与 %s %s建立连接\n' % self.client_address)
                        self.connection.setblocking(False)  
                        self.inputs.append(self.connection)  
  
                        # 给连接一个队列，该队列用于发送数据 
                        message_queues[self.connection] = Queue.Queue() 
                else: 
                    data = s.recv(1024) 
                    try:
                        message = json.loads(data)
                        if message:  
                            print message
                            # message.update(self.clients)
                            if message.has_key('terminal') and message['terminal'] == 'true':
                                if self.clients.has_key('A_ip'):
                                    self.clients['B_ip'] = self.client_address
                                self.clients['A_ip'] = self.client_address
                            # 客户端有数据发送   
                            # wx.CallAfter(Publisher().sendMessage, "update_t", message)
                            # message_queues[s].put(data)
                            # Add output channel for response    
                            if s not in outputs:
                                outputs.append(s)

                        if message.has_key('gateway'):
                            if message['gateway'] == 'false':
                                name = '信关站'
                        if message.has_key('terminal'):
                            if message['terminal'] == 'false':
                                name = '终端'
                                if self.clients.has_key('B_ip'):
                                    print 'bbb'
                                    del self.clients['B_ip']
                                else:
                                    print 'aaa'
                                    del self.clients['A_ip']
                        print self.clients
                    except:  
                        print "客户端没有数据发送，关闭连接"
                        # self.DisplayText.AppendText(u'关闭与%s %s的连接\n\n' % client_address)
                        wx.CallAfter(Publisher().sendMessage, "update", u'关闭与%s的连接\n\n' % name)  
                        
                        # 停止对该连接的读socket监听  
                        if s in outputs:  
                            outputs.remove(s)  
                        self.inputs.remove(s)  
                        s.close()  
                        # 移除消息队列  
                        del message_queues[s]  

                    merge_message = dict(message.items()+self.clients.items())
                    wx.CallAfter(Publisher().sendMessage, "update_t", merge_message)
            # 写socket处理 
            for s in writable:  
                try:  
                    next_msg = message_queues[s].get_nowait()  
                except Queue.Empty:  
                    # 如果消息队列没有消息，则停止写socket 
                    outputs.remove(s)  
                else:  
                    #如果消息队列有消息，则向客户端写
                    wx.CallAfter(Publisher().sendMessage, "update", u'向%s发送消息:%s' % (s.getpeername(), next_msg))  
                    s.send(next_msg)  

            #异常错误处理 
            for s in exceptional:
                wx.CallAfter(Publisher().sendMessage, "update", u'与%s的连接出现异常错误'% s.getpeername())  
                # 停止对该连接的读socket监听 
                self.inputs.remove(s)  
                if s in outputs:  
                    outputs.remove(s)  
                s.close()  
                # 移除消息队列  
                del message_queues[s]  
  
    def OnCloseWindow(self, event):
        self.Destroy()

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(parent=None, id=-1)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

if __name__ == "__main__":
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"
    app = MyApp()
    app.MainLoop()

