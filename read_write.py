import os

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import *                    # Uses Dynamixel SDK library
import curses

# Control table address
# ADDR_MX_TORQUE_ENABLE      = 64               # Control table address is different in Dynamixel model

ADDR_MX_TORQUE_ENABLE      = 24               # Control table address is different in Dynamixel model
# ADDR_MX_GOAL_POSITION      = 116
ADDR_MX_GOAL_POSITION      = 30 
# ADDR_MX_PRESENT_POSITION   = 132
ADDR_MX_PRESENT_POSITION   = 36 


# Protocol version
PROTOCOL_VERSION            = 1.0               # See which protocol version is used in the Dynamixel

# Default setting
DXL_ID                      = 1                 # Dynamixel ID : 1
# BAUDRATE                    = 57600             # Dynamixel default baudrate : 57600
BAUDRATE                    = 1000000
DEVICENAME                  = '/dev/ttyUSB0'    # Check which port is being used on your controller
                                                # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

TORQUE_ENABLE               = 1                 # Value for enabling the torque
TORQUE_DISABLE              = 0                 # Value for disabling the torque
DXL_MINIMUM_POSITION_VALUE  = 10           # Dynamixel will rotate between this value
DXL_MAXIMUM_POSITION_VALUE  = 4000            # and this value (note that the Dynamixel would not move when the position value is out of movable range. Check e-manual about the range of the Dynamixel you use.)
DXL_MOVING_STATUS_THRESHOLD = 20                # Dynamixel moving status threshold

index = 0
dxl_goal_position = [DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE]         # Goal position


# Initialize PortHandler instance
# Set the port path
# Get methods and members of PortHandlerLinux or PortHandlerWindows
portHandler = PortHandler(DEVICENAME)

# Initialize PacketHandler instance
# Set the protocol version
# Get methods and members of Protocol1PacketHandler or Protocol2PacketHandler
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port
if portHandler.openPort():
    print("Succeeded to open the port")
else:
    print("Failed to open the port")
    print("Press any key to terminate...")
    getch()
    quit()


# Set port baudrate
if portHandler.setBaudRate(BAUDRATE):
    print("Succeeded to change the baudrate")
else:
    print("Failed to change the baudrate")
    print("Press any key to terminate...")
    getch()
    quit()

# Enable Dynamixel Torque
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))
else:
    print("Dynamixel has been successfully connected")

stdscr = curses.initscr()


while 1:
    # print("Press any key to continue! (or press ESC to quit!)")

    print("Press 'a' motor rotate+100")
    print("Press 's' motor rotate-100")
    print("Press 'esc' exit program")
    if getch() == 'a':
        dxl_goal_position[index] += 100
    elif getch() == 's':
        dxl_goal_position[index] -= 100
    elif getch() == chr(0x1b):
        break

    # Write goal position
    # packetHandler.write4ByteTxRx:引数で設定したモータを目標角度まで動かす
    # dxl_goal_position[index]：目標角度
    dxl_comm_result, dxl_error = packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, dxl_goal_position[index])

    # COMMポートエラー時のメッセージ
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    # 目標角度がモータの範囲外時のメッセージ
    elif dxl_error != 0:
        print("%s" % packetHandler.getRxPacketError(dxl_error))

    while 1:
        # Read present position
        # モータの現在値dxl_present_positonを更新する
        dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)
        if dxl_comm_result != COMM_SUCCESS:
            print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
        elif dxl_error != 0:
            print("%s" % packetHandler.getRxPacketError(dxl_error))

        print("[ID:%03d] GoalPos:%03d  PresPos:%03d index:%d" % (DXL_ID, dxl_goal_position[index], dxl_present_position, index))

        # 終了判定
        # 指定角度まで動いたら終了　誤差はDXL_MOVING_STATUS_THRESHOLD値まで許容
        if not abs(dxl_goal_position[index] - dxl_present_position) > DXL_MOVING_STATUS_THRESHOLD:
            break
        # MX-12Wは下限値０なので、目標値が0以下のとき終了
        if dxl_goal_position[index] < 0:
            print("目標値が下限値以下です")
            break
        # MX-12Wは上限値が4095なので、目標値が4095以上のとき終了
        if 4095 < dxl_goal_position[index]:
            print("目標値が上限値以上です")
            break

    # # Change goal position
    # if index == 0:
    #     index = 1
    # else:
    #     index = 0



# Disable Dynamixel Torque
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
if dxl_comm_result != COMM_SUCCESS:
    print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("%s" % packetHandler.getRxPacketError(dxl_error))

# Close port
portHandler.closePort()