from control_panel import ControlPanel


def main():
    try:
        panel = ControlPanel('./data')
        panel.run()
    except IOError:
        print('It seems you have file named \'data\' in this directory. Please remove it and run this script again')


if __name__ == "__main__":
    main()
