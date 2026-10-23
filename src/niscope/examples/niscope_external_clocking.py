#!/usr/bin/python

import argparse
import niscope
import pytest
import sys


def _create_chart(plt):
    figure, axes = plt.subplots()
    (line,) = axes.plot([])
    axes.set_title('Waveform')
    axes.set_xlabel('Time (s)')
    axes.set_ylabel('Voltage (V)')
    axes.grid(True)
    figure.tight_layout()
    return figure, axes, line


def _update_chart(axes, line, waveforms, actual_sample_rate):
    for waveform in waveforms:
        x = [waveform.relative_initial_x + i * waveform.x_increment for i in range(len(waveform.samples))]
        line.set_data(x, waveform.samples)
    axes.set_title(f'Waveform (Actual Sample Rate: {actual_sample_rate:g} S/s)')
    axes.relim()
    axes.autoscale_view()


def example(resource_name, channels, options, length, voltage, offset, source, rate, divisor, multiplier, total_iterations):
    # Imported lazily because matplotlib is unavailable on some platforms (e.g. 32-bit Python)
    import matplotlib.pyplot as plt

    with niscope.Session(resource_name=resource_name, options=options) as session:
        channel_session = session.channels[channels]
        channel_session.configure_vertical(range=voltage, coupling=niscope.VerticalCoupling.DC, offset=offset)
        session.configure_trigger_immediate()
        session.horz_min_num_pts = length
        session.samp_clk_timebase_src = source
        session.samp_clk_timebase_rate = rate
        session.samp_clk_timebase_div = divisor
        session.sample_clock_timebase_multiplier = multiplier

        figure, axes, line = _create_chart(plt)

        iterations = 0
        try:
            # A total_iterations of None runs until the chart window is closed or Ctrl+C is pressed
            while plt.fignum_exists(figure.number) and (total_iterations is None or iterations < total_iterations):
                # read() initiates the acquisition, waits for it to complete and fetches the data
                waveforms = channel_session.read(num_samples=length)
                _update_chart(axes, line, waveforms, session.horz_sample_rate)
                iterations += 1
                plt.pause(0.01)

            # The acquisition has stopped; keep the final chart on screen until its window is closed
            if total_iterations is not None and plt.fignum_exists(figure.number):
                plt.show()
        except KeyboardInterrupt:
            pass
        finally:
            plt.close(figure)


def _main(argsv):
    parser = argparse.ArgumentParser(description='Continuously acquires and plots a waveform using an external sample clock.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--resource-name', default='PXI1Slot2', help='Resource name of an NI digitizer.')
    parser.add_argument('-c', '--channels', default='0', help='Channel(s) to use')
    parser.add_argument('-l', '--length', default=1000, type=int, help='Specifies the minimum number of points you require in the waveform record for each channel.')
    parser.add_argument('-v', '--voltage', default=1.0, type=float, help='Specifies the vertical range of the input signal in volts.')
    parser.add_argument('--offset', default=0.0, type=float, help='Specifies the location of the center of the range in volts, with respect to ground.')
    parser.add_argument('-s', '--source', default='VAL_CLK_IN', type=str, help='Specifies the source of the sample clock timebase, which is the timebase used to control waveform sampling.')
    parser.add_argument('-r', '--rate', default=1e8, type=float, help='Specifies the frequency in hertz of the external clock used as the timebase source.')
    parser.add_argument('-d', '--divisor', default=1, type=int, help='Specifies the ratio between the sample clock timebase rate and the actual sample rate, which can be slower.')
    parser.add_argument('-m', '--multiplier', default=1, type=int, help='Specifies the ratio between the sample clock timebase rate and the actual sample rate, which can be higher.')
    parser.add_argument('--total-iterations', default=None, type=int, help='Stops after this many acquisitions and keeps the chart open until its window is closed; omit to run until the chart window is closed or Ctrl+C is pressed.')
    parser.add_argument('-op', '--option-string', default='', type=str, help='Option string')
    args = parser.parse_args(argsv)
    example(args.resource_name, args.channels, args.option_string, args.length, args.voltage, args.offset, args.source, args.rate, args.divisor, args.multiplier, args.total_iterations)


def main():
    _main(sys.argv[1:])


def test_example():
    plt = pytest.importorskip('matplotlib.pyplot')
    plt.switch_backend('Agg')  # Avoid opening a chart window during the test
    options = {'simulate': True, 'driver_setup': {'Model': '5164', 'BoardType': 'PXIe', }, }
    example('PXI1Slot2', '0', options, 1000, 1.0, 0.0, 'VAL_CLK_IN', 1e8, 1, 1, 2)


def test_main():
    plt = pytest.importorskip('matplotlib.pyplot')
    plt.switch_backend('Agg')  # Avoid opening a chart window during the test
    cmd_line = ['--option-string', 'Simulate=1, DriverSetup=Model:5164; BoardType:PXIe', '--total-iterations', '2', ]
    _main(cmd_line)


if __name__ == '__main__':
    main()
