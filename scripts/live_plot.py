# Bokeh app to plot 2x6 live joint data using bokeh serve
# bokeh serve --show live_plot.py
#$WORKSPACE_ROOT/venv/bin/bokeh serve --show live_plot.py
from functools import partial
from multiprocessing import Process, Queue
import numpy as np
import os
import time

from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, CheckboxGroup, CustomJS, Button, DataRange1d
from bokeh.layouts import gridplot, column, row
from bokeh.io.export import export_png
from bokeh.models import Div
from bokeh.events import ButtonClick

import rclpy
from rclpy.node import Node
from control_msgs.msg import JointTrajectoryControllerState
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from builtin_interfaces.msg import Time as MsgTime
from multiprocessing import Queue
from rclpy.time import Time, Duration

UI_UPDATE = 500  # ms (2 Hz)
SAMPLE_RATE = 20
MIN_UPDATE_PERIOD = (10**9)/SAMPLE_RATE  # 20 Hz
TIME_WINDOW_SECONDS = 10  # Seconds
ROLLOVER_WINDOW = int(TIME_WINDOW_SECONDS * SAMPLE_RATE)  # Samples x seconds
JOINT_STATES_TOPIC = '/m1n6s200/joint_states'  # ''
if os.environ.get("ROS_DISTRO") == 'iron':
    print("Using ROS 2 Iron setup topics ")
    JOINT_STATES_TOPIC = '/joint_states'

CONTROLLER_STATES_TOPIC = '/mico_arm_controller/controller_state'
JOINT_NAMES = [
    'm1n6s200_joint_1', 'm1n6s200_joint_2', 'm1n6s200_joint_3',
    'm1n6s200_joint_4', 'm1n6s200_joint_5', 'm1n6s200_joint_6'
]


class ROSJointDataCollector(Node):
    def __init__(self, joints_queue, trajectory_queue, joint_names):
        super().__init__('joint_data_collector')
        self.queue = joints_queue
        self.traj_queue = trajectory_queue
        self.joint_names = joint_names
        self.latest_command = {name: {'pos_cmd': 0.0, 'vel_cmd': 0.0} for name in joint_names}
        self.time_start = None
        self.last_update = None
        # self.create_subscription(JointState, JOINT_STATES_TOPIC, self.joint_state_callback, 10)
        self.create_subscription(JointTrajectoryControllerState, CONTROLLER_STATES_TOPIC, self.controller_state_callback, 10)
        self.create_subscription(JointTrajectory, '/mico_arm_controller/joint_trajectory', self.trajectory_callback, 10)

    def _msgtime_to_nanoseconds(self, msg_time: MsgTime):
        time = self.get_clock().now().nanoseconds
        if msg_time is not None:
            time = Time.from_msg(msg_time).nanoseconds
            if time != 0:
                time = self.get_clock().now().nanoseconds
                if self.time_start is None:
                    self.time_start = time
                    self.last_update = -10
        return time - self.time_start

    def trajectory_callback(self, msg):
        # print("Trajectory callback ...", flush=True)
        traj_start = self._msgtime_to_nanoseconds(msg.header.stamp)
        self.traj_queue.put(('clear', None, None, None, None))
        for point in msg.points:
            point_time = traj_start + Duration.from_msg(point.time_from_start).nanoseconds
            for i, name in enumerate(msg.joint_names):
                if name in self.joint_names:
                    pos_cmd = point.positions[i] if i < len(point.positions) else 0.0
                    vel_cmd = point.velocities[i] if i < len(point.velocities) else 0.0
                    # Push future trajectory point into the queue for plotting
                    self.traj_queue.put(('traj', point_time, name, pos_cmd, vel_cmd))

    def joint_state_callback(self, msg):
        #print("Joint states callback ...", flush=True)
        time = self._msgtime_to_nanoseconds(msg.header.stamp)
        if (time - self.last_update) < MIN_UPDATE_PERIOD:
            return  # Only update at 20 Hz max
        joint_data = {}
        #print(f"msg = {msg.name}, {msg.position}, {msg.velocity}")
        for name, pos, vel in zip(msg.name, msg.position, msg.velocity):
            if name in self.joint_names:
                joint_data[name] = {
                    'pos': pos,
                    'vel': vel,
                    'ref_pos': None,
                    'ref_vel': None,
                    'cmd_vel': None
                }
        if joint_data:
            self.queue.put(('actual', time, joint_data))
            print(f"put called at {time} with {self.queue.qsize()} items in queue\n{joint_data}", flush=True)
            self.last_update = time

    def controller_state_callback(self, msg):
        #print("Joint states callback ...", flush=True)
        time = self._msgtime_to_nanoseconds(msg.header.stamp)
        if (time - self.last_update) < MIN_UPDATE_PERIOD:
            return  # Only update at 20 Hz max
        joint_data = {}
        for name, pos, vel, ref_pos, ref_vel, cmd_vel in zip(msg.joint_names,
                                                    msg.feedback.positions, msg.feedback.velocities,
                                                    msg.reference.positions, msg.reference.velocities,
                                                    msg.output.velocities):  # Assuming velocity interface
            if name in self.joint_names:
                joint_data[name] = {
                    'pos': pos,
                    'vel': vel,
                    'ref_pos': ref_pos,
                    'ref_vel': ref_vel,
                    'cmd_vel': cmd_vel
                }
        if joint_data:
            self.queue.put(('actual', time, joint_data))
            self.last_update = time
            # print(f"put called at {time} with {self.queue.qsize()} items in queue", flush=True)

def run_ros_node(joints_queue, traj_queue, joint_names):
    rclpy.init()
    node = ROSJointDataCollector(joints_queue, traj_queue, joint_names)
    print("Spin the ROS node ...", flush=True)
    rclpy.spin(node)

    print("Done spinning the ROS node ... shutdown!", flush=True)
    node.destroy_node()
    rclpy.shutdown()


joints_data_queue = Queue()
traj_data_queue = Queue()

# Create 1 ColumnDataSources

joint_source_data = {'t': []}
traj_source_data = {'tt': []}
for jnt, name in enumerate(JOINT_NAMES):
    joint_source_data[f'pos_{jnt}'] = []
    joint_source_data[f'vel_{jnt}'] = []
    joint_source_data[f'ref_pos_{jnt}'] = []
    joint_source_data[f'ref_vel_{jnt}'] = []
    joint_source_data[f'cmd_vel_{jnt}'] = []

    traj_source_data[f'pos_cmd_{jnt}'] = []
    traj_source_data[f'vel_cmd_{jnt}'] = []


joint_sources = ColumnDataSource(data=joint_source_data)

traj_sources = ColumnDataSource(data=traj_source_data)

delay_div = Div(text="Delay text ...", width=100, height=40)
time_source_data = {'now': [0]}
time_source = ColumnDataSource(data=time_source_data)
time_source.js_on_change('data', CustomJS(args=dict(source=time_source, delay_div=delay_div), code="""
    const now = Date.now();  // ms of wall clock
    const py_time = source.data['now'][0];
    const delay = now - py_time;

    let color = "darkgreen";
    if (delay > 500) {
        color = "red";
    } else if (delay > 200) {
        color = "orangered";
    }

    delay_div.text = `<b>Delay:</b> <span style="color:${color};">${delay} ms</span>`;
    console.log("JS callback triggered: ", delay);
    source.change.emit();
"""))

# Toggle checkbox to show/hide future trajectory
future_toggle = CheckboxGroup(labels=["Show Future Trajectory"], active=[0])

# Create figures and arrange them flat (not nested)
posn_plots = []
vel_plots = []
plot_refs = []  # For exporting

for jnt, name in enumerate(JOINT_NAMES):
    p_pos = figure(title=f"{name} Position", x_axis_label="Time (s)", y_axis_label="Position (rad)",
                y_range=(-1.5*np.pi, 1.5*np.pi),
                tools="pan,wheel_zoom,box_zoom,reset",
                active_scroll="wheel_zoom", sizing_mode="stretch_both")
    future_line_pos = p_pos.line('tt', f'pos_cmd_{jnt}', source=traj_sources,
                                color='maroon', line_dash='dashed', legend_label='Trajectory')
    p_pos.line('t', f'ref_pos_{jnt}', source=joint_sources, color='red', legend_label='Reference')
    p_pos.line('t', f'pos_{jnt}', source=joint_sources, color='blue', legend_label='Actual')
    p_pos.legend.click_policy = 'hide'
    p_pos.legend.background_fill_alpha = 0.3  # Semi-transparent
    posn_plots.append(p_pos)

    p_vel = figure(title=f"{name} Velocity", x_axis_label="Time (s)", y_axis_label="Velocity (rad/s)",
                    y_range=(-1.5*np.pi, 1.5*np.pi),
                    tools="pan,wheel_zoom,box_zoom,reset",
                    active_scroll="wheel_zoom", sizing_mode="stretch_both")
    future_line_vel = p_vel.line('tt', f'vel_cmd_{jnt}', source=traj_sources,
                                color='maroon', line_dash='dashed', legend_label='Trajectory')
    p_vel.line('t', f'cmd_vel_{jnt}', source=joint_sources , color='cyan', legend_label='Command')
    p_vel.line('t', f'ref_vel_{jnt}', source=joint_sources, color='red', legend_label='Reference')
    p_vel.line('t', f'vel_{jnt}', source=joint_sources, color='blue', legend_label='Actual')
    p_vel.legend.click_policy = 'hide'
    p_vel.legend.background_fill_alpha = 0.3  # Semi-transparent
    vel_plots.append(p_vel)

    def toggle_visibility(attr, old, new, fl=future_line_pos, flv=future_line_vel):
        visible = 0 in future_toggle.active
        fl.visible = visible
        flv.visible = visible

    future_toggle.on_change('active', toggle_visibility)

# Use flat list of plots with ncols=6
plot_refs = posn_plots + vel_plots
grid = gridplot(plot_refs, ncols=6, sizing_mode="stretch_both")

reset_button = Button(label="Reset Plots", button_type="success")

def reset_all():
    for p in plot_refs:
        p.x_range = DataRange1d()
        p.y_range = DataRange1d(start=-1.5*np.pi, end=1.5*np.pi)
        # Reset all legend-hidden glyphs to visible
        for r in p.renderers:
            if hasattr(r, 'visible'):
                r.visible = True

reset_button.on_click(reset_all)

# # Export button
# export_button = Button(label="Export PNG", button_type="success")
# def export_all():
#     for i, plot in enumerate(posn_plots):
#         export_png(plot, filename=f"joint_{i}_posn_plot.png")
#     for i, plot in enumerate(vel_plots):
#         export_png(plot, filename=f"joint_{i}_velocity_plot.png")
# export_button.on_click(export_all)

status_div = Div(text="Status: waiting for data...", width=420, height=40)
dummy_plot = figure(height=0, width=0)  # invisible
dummy_plot.scatter(x='now', y='now', source=time_source, size=0)  # invisible glyph

layout = column(row(future_toggle, reset_button), row(status_div, delay_div), grid, dummy_plot, sizing_mode="stretch_both")
curdoc().add_root(layout)

# Update function
def update():
    now = time.time()
    # print(f"update called at {now} with {joints_data_queue.qsize()} items in queue", flush=True)
    joints_qsize = joints_data_queue.qsize()
    if joints_qsize == 0:
        # Wait for joint data before doing any streaming
        return

    # Create flat arrays per column
    stream_dict = {'t': []}
    for jnt in range(len(JOINT_NAMES)):
        stream_dict[f'pos_{jnt}'] = []
        stream_dict[f'vel_{jnt}'] = []
        stream_dict[f'ref_pos_{jnt}'] = []
        stream_dict[f'ref_vel_{jnt}'] = []
        stream_dict[f'cmd_vel_{jnt}'] = []

    while not joints_data_queue.empty():
        msg = joints_data_queue.get()
        if msg[0] == 'actual':
            _, t, joint_data = msg
            stream_dict['t'].append(t * 1.e-9)

            for jnt, name in enumerate(JOINT_NAMES):
                stream_dict[f'pos_{jnt}'].append(joint_data[name]['pos'])
                stream_dict[f'vel_{jnt}'].append(joint_data[name]['vel'])
                stream_dict[f'ref_pos_{jnt}'].append(joint_data[name]['ref_pos'])
                stream_dict[f'ref_vel_{jnt}'].append(joint_data[name]['ref_vel'])
                stream_dict[f'cmd_vel_{jnt}'].append(joint_data[name]['cmd_vel'])

    # Only call stream once per update
    if stream_dict['t']:
        joint_sources.stream(stream_dict, rollover=ROLLOVER_WINDOW)

    if len(joint_sources.data['t']) > 0:
        latest_t = joint_sources.data['t'][-1]
    else:
        latest_t = 0

    now_str = time.strftime("%H:%M:%S", time.localtime(now)) + f".{int((now % 1)*1000):03d}"
    status_text = (f"<b>Last update:</b> {now_str} ({latest_t:.6f} s) &nbsp; | "
                f"<b>Joint queue:</b> {joints_qsize} &nbsp; | "
                f"<b>Traj queue:</b> {traj_data_queue.qsize()} &nbsp; |")
    status_div.text = status_text
    print(status_text.replace("<b>","").replace("</b>", "").replace("&nbsp;", "").replace("<span style='color:","").replace(";'>", "").replace("</span>",""))

    time_source.data['now'][0] = int(now*1000.0)
    time_source.trigger('data', time_source.data, time_source.data)  # tell Bokeh to refresh JS side

    stream_dict = {'tt': []}
    for jnt in range(len(JOINT_NAMES)):
        stream_dict[f'pos_cmd_{jnt}'] = []
        stream_dict[f'vel_cmd_{jnt}'] = []

    while not traj_data_queue.empty():
        msg = traj_data_queue.get()
        if msg[0] == 'traj':
            # print(f"{msg}")
            _, t, name, pos_cmd, vel_cmd = msg
            t *= 1.e-9
            if t not in stream_dict['tt']:
                if t > (latest_t + TIME_WINDOW_SECONDS):
                    # print(f"Limit trajectory to {t} with {traj_data_queue.qsize()} points remaining")
                    break  # Only show a portion ahead

                ndx = len(stream_dict['tt'])
                stream_dict['tt'].append(t)
                for jnt in range(len(JOINT_NAMES)):
                    if len(traj_sources.data[f'pos_cmd_{jnt}']) > 0:
                        # Initialize with the old data
                        stream_dict[f'pos_cmd_{jnt}'].append(traj_sources.data[f'pos_cmd_{jnt}'][-1])
                        stream_dict[f'vel_cmd_{jnt}'].append(traj_sources.data[f'vel_cmd_{jnt}'][-1])
                    else:
                        stream_dict[f'pos_cmd_{jnt}'].append(1.2345)
                        stream_dict[f'vel_cmd_{jnt}'].append(1.2345)

            else:
                ndx = len(stream_dict['tt']) - 1

            try:
                jnt = JOINT_NAMES.index(name)
                stream_dict[f'pos_cmd_{jnt}'][ndx] = pos_cmd
                stream_dict[f'vel_cmd_{jnt}'][ndx] = vel_cmd
            except Exception as exc:
                print(f"Invalid joint name '{name}' ({jnt}) {exc}")

        elif msg[0] == 'clear':
            print("New trajectory data incoming ...")
            cleared = {'tt': []}
            for jnt in range(len(JOINT_NAMES)):
                cleared[f'pos_cmd_{jnt}'] = []
                cleared[f'vel_cmd_{jnt}'] = []
            traj_sources.data = cleared

    # Only call stream once per update
    if stream_dict['tt']:
        # print(f"traj: {stream_dict}")
        tt = np.array(traj_sources.data['tt'])
        cmd = np.array(traj_sources.data['pos_cmd_0'])
        if None in tt or None in cmd:
            print(f'tt={tt}')
            print(f'pos 0 = {cmd}')
        elif np.isnan(tt).any() or np.isnan(cmd).any():
            print("NaNs in tt:", np.isnan(tt).any())
            print("NaNs in cmd:", np.isnan(cmd).any())

        if len(tt) > 0 and np.any(np.diff(tt) < 0.0001):
            print("tt diff:", np.diff(tt))
            print("tt min:", np.min(tt), "tt max:", np.max(tt))
        traj_sources.stream(stream_dict, rollover=ROLLOVER_WINDOW)

curdoc().add_periodic_callback(partial(update), 250)

# Launch ROS subscriber in background
ros_proc = Process(target=run_ros_node, args=(joints_data_queue, traj_data_queue, JOINT_NAMES))
ros_proc.start()

