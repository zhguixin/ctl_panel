#!/usr/bin/env python
#coding=utf-8
#################################
#   Copyright 2014.7.23
#       fly_video lihao
#   @author: 345570600@qq.com
#################################
from gnuradio import audio
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import lte_sat

import wx  
import sys
import threading
import multiprocessing
from multiprocessing import Queue
import socket,select
import json
import traceback,time
import ConfigParser
from wx.lib.pubsub import Publisher 

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

from matplotlib.widgets import SpanSelector
class MatplotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.figure = Figure()
        # self.axes = self.figure.add_subplot(1,1,1)
        # self.axes = self.figure.gca(projection='3d')
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.toolbar=NavigationToolbar2Wx(self.canvas)
        self.toolbar.AddLabelTool(5,'',wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, (32,32)))

        self.toolbar.Realize()      

        self.cb_grid = wx.CheckBox(self, -1, 
            "显示网格",
            style=wx.ALIGN_RIGHT)
        # self.Bind(wx.EVT_CHECKBOX, self.on_cb_grid, self.cb_grid)

        self.button1 = wx.Button(self, -1, "按钮1")
        self.button2 = wx.Button(self, -1, "按钮2")
        self.button3 = wx.Button(self, -1, "按钮3")
        self.button4 = wx.Button(self, -1, "按钮4")
        self.Bind(wx.EVT_BUTTON,self.draw,self.button1)
        self.Bind(wx.EVT_BUTTON,self.draw_scatter,self.button2)
        self.Bind(wx.EVT_BUTTON,self.draw_3d,self.button3)
        self.Bind(wx.EVT_BUTTON,self.draw_plot,self.button4)
        
        ########开始布局############
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(self.button1,1,wx.EXPAND)
        sizer1.Add(self.button2,1,wx.EXPAND)
        sizer1.Add(self.button3,1,wx.EXPAND)
        sizer1.Add(self.button4,1,wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(wx.StaticLine(self), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
        self.sizer.Add(sizer1, 0, wx.EXPAND)
        self.sizer.Add(wx.StaticLine(self), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
        self.sizer.Add(self.cb_grid,0,wx.ALIGN_RIGHT)
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

    def draw(self,event):
        self.figure.clear() 
        self.axes = self.figure.add_subplot(111)
        self.axes.clear() 
        self.axes.grid(self.cb_grid.IsChecked())

        t = np.arange(0.0, 3.0, 0.01)
        self.axes.plot(t)
        self.canvas.draw()
        # self.canvas.Refresh()

    def draw_scatter(self,event):
        self.figure.clear() 
        self.axes = self.figure.add_subplot(111)
        self.axes.clear()
        self.axes.grid(self.cb_grid.IsChecked())

        f = open ( '/home/lh/matplotlib/dat/subf_has_sr.dat' , 'rb' )
        x = np.fromfile ( f , dtype = np.float32 , count = 10000 )
        f.close()

        n = len ( x ) / 2

        """ break x into two arrays    """
        """ or reshape x to ( 2 , n )  """
        x = x.reshape ( 2 , n )

        """ Reconstruct the original complex array """
        wfc = np.zeros ( [ n ] , dtype = np.complex )
        wfc.real = x [ 0 ]
        wfc.imag = x [ 1 ]

        self.axes.scatter( wfc.real, wfc.imag, facecolor='blue' )
        self.canvas.draw()
        # plt.show()

    def draw_3d(self,event):
        self.figure.clear() 
        self.axes = self.figure.add_subplot(111)
        self.axes = self.figure.gca(projection='3d')
        self.axes.clear() 
        self.axes.grid(self.cb_grid.IsChecked())

        X = np.arange(-5, 5, 0.25)
        Y = np.arange(-5, 5, 0.25)
        X, Y = np.meshgrid(X, Y)
        R = np.sqrt(X**2 + Y**2)
        Z = np.sin(R)
        surf = self.axes.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                linewidth=0, antialiased=False)
        self.axes.set_zlim(-1.01, 1.01)

        self.axes.zaxis.set_major_locator(LinearLocator(10))
        self.axes.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

        self.figure.colorbar(surf, shrink=0.5, aspect=5)

        self.canvas.draw()

    def draw_plot(self,event):
        self.figure.clear() 
        self.axes = self.figure.add_subplot(211, axisbg='#FFFFCC')
        self.axes.clear()
        self.axes.grid(self.cb_grid.IsChecked())

        x = np.arange(0.0, 5.0, 0.01)
        y = np.sin(2*np.pi*x) + 0.5*np.random.randn(len(x))

        self.axes.plot(x, y, '-')
        self.axes.set_ylim(-2,2)
        self.axes.set_title('Press left mouse button and drag to test')

        self.axes2 = self.figure.add_subplot(212, axisbg='#FFFFCC')
        self.axes2.clear()
        self.axes2.grid(self.cb_grid.IsChecked())
        line2, = self.axes2.plot(x, y, '-')


        def onselect(xmin, xmax):
            indmin, indmax = np.searchsorted(x, (xmin, xmax))
            indmax = min(len(x)-1, indmax)

            thisx = x[indmin:indmax]
            thisy = y[indmin:indmax]
            line2.set_data(thisx, thisy)
            self.axes2.set_xlim(thisx[0], thisx[-1])
            self.axes2.set_ylim(thisy.min(), thisy.max())
            self.figure.canvas.draw()

        # set useblit True on gtkagg for enhanced performance
        self.span = SpanSelector(self.axes, onselect, 'horizontal', useblit=True,
                            rectprops=dict(alpha=0.5, facecolor='red') )

        self.figure.canvas.draw()
        # plt.show()

class MainFrame(wx.Frame):
    def __init__(self,parent,id):
        wx.Frame.__init__(self, None, title=u"信关站界面", size=(1000,600))
        self.Centre()
        self.SetBackgroundColour("white")

        self.sp = wx.SplitterWindow(self)
        self.panel = wx.Panel(self.sp, style=wx.SP_3D)
        self.p1 = MatplotPanel(self.sp)
        self.sp.SplitVertically(self.panel,self.p1,400)
        # self.p1.draw_scatter()

        self.gateway_config = ConfigParser.ConfigParser()
        self.gateway_config.read("gateway.conf")
        
        #创建面板
        self.createframe()

        # 创建一个pubsub接收器,用于接收从子线程传递过来的消息
        Publisher().subscribe(self.updateDisplay, "update")

    def updateDisplay(self, msg): 
        """
        从线程接收数据并且在界面更新显示
        """
        dict_status = msg.data
        if dict_status['pss_status']:
            self.pss_status.SetValue("锁定")
        else:
            self.pss_status.SetValue("未锁定")
        if dict_status['sss_status']:
            self.sss_status.SetValue("锁定")
        else:
            self.sss_status.SetValue("未锁定")
        if dict_status['pbch_status']:
            self.pbch_status.SetValue("锁定")
        else:
            self.pbch_status.SetValue("未锁定")
        if dict_status['process_state']==1:
            self.process_state.SetValue("跟踪")
        elif dict_status['process_state']==0:
            self.process_state.SetValue("捕获")
        self.cfo.SetValue(str(dict_status['cfo']))
        self.fte.SetValue(str(dict_status['fte']))
        self.pss_pos.SetValue(str(dict_status['pss_pos']))


    def createframe(self):

        #绑定窗口的关闭事件
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        #主同步状态是否锁定
        pss_status_st = wx.StaticText(self.panel, -1, u"主同步状态:")
        self.pss_status = wx.TextCtrl(self.panel, -1, "未锁定", size=(130,30), style=wx.TE_READONLY)

        #辅同步状态是否锁定
        sss_status_st = wx.StaticText(self.panel, -1, u"辅同步状态:")
        self.sss_status = wx.TextCtrl(self.panel, -1, "未锁定", style=wx.TE_READONLY)

        #pbch是否找到
        pbch_status_st = wx.StaticText(self.panel, -1, u"当前pbch状态:")
        self.pbch_status = wx.TextCtrl(self.panel, -1, "pbch未找到", style=wx.TE_READONLY)

        #当前处理状态
        process_state_st = wx.StaticText(self.panel, -1, u"当前处理状态:")
        self.process_state = wx.TextCtrl(self.panel, -1, "捕获", style=wx.TE_READONLY)

        #实时载波频率偏差值
        cfo_st = wx.StaticText(self.panel, -1, u"实时载波频率偏差:")
        self.cfo = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)

        #实时细定时误差
        fte_st = wx.StaticText(self.panel, -1, u"实时细定时误差:")
        self.fte = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)

        #峰值位置
        pss_pos_st = wx.StaticText(self.panel, -1, u"峰值位置:")
        self.pss_pos = wx.TextCtrl(self.panel, -1, "0", style=wx.TE_READONLY)

        #连接按钮
        self.connect_button = wx.Button(self.panel, -1, u"连接")
        self.Bind(wx.EVT_BUTTON, self.OnConnect, self.connect_button)  
        self.connect_button.SetDefault() 

        #设置连接服务器的IP地址和端口号
        self.gateway_config.read("gateway.conf")
        try: s_ip = self.gateway_config.get("address", "s_ip")
        except: s_ip = '192.168.139.180'

        try: s_port = self.gateway_config.get("address", "s_port")
        except: s_port = '7000'

        ip_st = wx.StaticText(self.panel, -1, u"IP地址 :")  
        self.IPText = wx.TextCtrl(self.panel, -1, s_ip)  
        port_st = wx.StaticText(self.panel, -1, u"端口号 :")  
        self.PortText = wx.TextCtrl(self.panel, -1, s_port)

        #######开始布局############
        sizer1 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer1.AddGrowableCol(1)
        sizer1.Add(pss_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.pss_status, 0, wx.EXPAND)
        sizer1.Add(sss_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.sss_status, 0, wx.EXPAND)
        sizer1.Add(pbch_status_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.pbch_status, 0, wx.EXPAND)
        sizer1.Add(process_state_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.process_state, 0, wx.EXPAND)
        sizer1.Add(cfo_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.cfo, 0, wx.EXPAND)
        sizer1.Add(fte_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.fte, 0, wx.EXPAND)
        sizer1.Add(pss_pos_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.pss_pos, 0, wx.EXPAND)

        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'状态显示'), wx.VERTICAL)
        sizer2.Add(sizer1, 0, wx.EXPAND | wx.ALL, 10)

        sizer3 = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        sizer3.AddGrowableCol(1)
        sizer3.Add(ip_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.IPText, 3, wx.EXPAND)
        sizer3.Add(port_st, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        sizer3.Add(self.PortText, 1, wx.EXPAND)

        #连接按钮
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add((20,20), 1)
        sizer4.Add(self.connect_button, 0, wx.ALIGN_RIGHT)

        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.NewId(), u'连接服务器'), wx.VERTICAL)
        sizer5.Add(sizer3, 0, wx.EXPAND | wx.ALL, 10)
        sizer5.Add(sizer4, 0, wx.EXPAND | wx.ALL, 10)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(sizer2,0,wx.EXPAND | wx.ALL, 25)
        box1.Add(wx.StaticLine(self.panel), 0,wx.EXPAND|wx.TOP|wx.BOTTOM,0)
        box1.Add(sizer5,0,wx.EXPAND | wx.ALL | wx.BOTTOM, 25)

        #自动调整界面尺寸
        self.panel.SetSizer(box1)

    def OnConnect(self, event):
        # self.connect_button.Disable()
        self.gateway_config.read("gateway.conf")
        if "address" not in self.gateway_config.sections():
            self.gateway_config.add_section("address")

        #address
        self.gateway_config.set("address", "s_ip", self.IPText.GetValue())
        self.gateway_config.set("address", "s_port", self.PortText.GetValue())

        #写入配置文件
        param_file = open("gateway.conf","w")
        self.gateway_config.write(param_file)
        param_file.close()

        self.port = int(self.PortText.GetValue())  
        self.host = str(self.IPText.GetValue()) 
        self.t_gateway = threading.Thread(target = self.client_gateway,args = (self.host,self.port))
        self.t_gateway.setDaemon(True)
        self.t_gateway.start()

    def client_gateway(self,host,port):
        self.host = host
        self.port = port 

        self.status = {}
        self.status['gateway'] = "true"

        self.t2 = threading.Thread(target = self.start_monitor_for_panel)
        self.t2.setDaemon(True)
        self.t2.start()

        self.start_client()

    def start_client(self):
        server_address = (self.host,self.port)
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client.connect(server_address)

        self.t3 = threading.Thread(target = self.start_monitor)
        self.t3.setDaemon(True)
        self.t3.start()

        # self.client.send('data_status')
        # 读socket
        self.inputs = [ self.client ] 

        # 写socket
        outputs = []

        # 消息队列
        self.message_queues = {} 

        while self.inputs:  
            readable, writable, exceptional = select.select(self.inputs, outputs, self.inputs)  
              
            #处理input
            for s in readable:  
                data = s.recv(2048) 

                if data: 
                    if data == 'start_block':
                        self.q = Queue()
                        self.p1 = multiprocessing.Process(name='start_top_block',
                                target=self.start_top_block)
                        self.p1.daemon = True
                        self.p1.start()

                    elif data == 'stop_block':
                        self.stop_top_block() 
                    else:
                        global param   
                        param = json.loads(data)
                        # A readable client socket has data  
                        print 'received param from ', s.getpeername() 
                        try:
                            if self.p1.is_alive():
                                #GNURadio模块运行过程中修改参数
                                self.threshold = float(param['Threshold'])
                                # self.tb.set_threshold(self.threshold)
                                self.q.put(self.threshold)
                        except:pass

                else:  
                    print 'closing after reading no data'
                    if s in outputs:  
                        outputs.remove(s)  
                    self.inputs.remove(s)  
                    s.close()  
                    # Remove message queue  
                    del self.message_queues[s]  

            # Handle outputs  
            for s in writable:  
                try:  
                    next_msg = self.message_queues[s].get_nowait()  
                except Queue.Empty:  
                    # No messages waiting so stop checking for writability.  
                    print 'output queue for', s.getpeername(), 'is empty'  
                    outputs.remove(s)  
                else:  
                    print 'sending "%s" to %s' % (next_msg, s.getpeername())  
                    s.send(next_msg)  
            # Handle "exceptional conditions"  
            for s in exceptional:  
                print 'handling exceptional condition for', s.getpeername()    
                # Stop listening for input on the connection  
                self.inputs.remove(s)  
                if s in outputs:  
                    outputs.remove(s)  
                s.close()  
                # Remove message queue  
                del self.message_queues[s]   
    
    # start_monitor函数的代码有两个作用，一个是通过callafter函数向gateway界面传递状态信息，
    # 另一个是通过socket.client向控制界面传递状态信息。
    def start_monitor_for_panel(self): 
        while True:
            try:
                if self.p1.is_alive():
                    self.status.update(self.q.get())
                    wx.CallAfter(Publisher().sendMessage, "update", self.status)
            except:pass
            time.sleep(1)

    def start_monitor(self):
        while True:
            data_status = json.dumps(self.status)
            self.client.send(data_status)
            time.sleep(1)

    #子进程
    def start_top_block(self):
        global param 
        if param['work_mod'] == '音频业务演示': 
            self.tb = dl_recv(**param)
        elif param['work_mod'] == '数据测试演示':
            self.tb = dl_ber_recv(**param)
        self.t1 = threading.Thread(target = self.monitor_forever)
        self.t1.setDaemon(True)
        self.t1.start()

        self.tb.start()
        self.tb.wait()

    def monitor_forever(self):
        
        while True:
            #从控制界面获取参数，动态改变
            # self.tb.set_threshold(self.q.get())

            #获取Gnuradio模块中的状态信息，传递至界面
            self.q.put(self.tb.get_status())
            time.sleep(1) 

    def stop_top_block(self):
        self.p1.terminate()
        print 'stop'

    def OnCloseWindow(self, event):
        try:
            self.status['gateway']="false"
            data_status = json.dumps(self.status)
            self.client.send(data_status)
            self.client.close() 
            self.Destroy()
        except:
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
