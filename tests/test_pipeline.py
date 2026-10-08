import csv
import json
import math
import tempfile
import unittest
from pathlib import Path
from roundness.pipeline import calculate, read_profile, run

CONFIG = dict(nominal_radius_mm=10, gain=.5, mode='bidirectional', removal_direction='radius_decrease', z_mm=2, max_compensation_um=100)
ERRORS = [20*math.cos(2*math.radians(a)) for a in range(360)]

class PipelineTests(unittest.TestCase):
    def test_inverse_and_coordinates(self):
        rows, report = calculate(ERRORS, CONFIG)
        self.assertAlmostEqual(rows[0][2], -10)
        self.assertAlmostEqual(rows[90][2], 10)
        self.assertAlmostEqual(rows[0][4], 9.99)
        self.assertAlmostEqual(rows[90][5], 10.01)
        self.assertAlmostEqual(report['fixed_datum_radial_pv_um'], 40)

    def test_removal_directions(self):
        for direction, low, high in [('radius_decrease', -20, 0), ('radius_increase', 0, 20)]:
            _, report = calculate(ERRORS, {**CONFIG, 'mode':'remove_only', 'removal_direction':direction})
            self.assertAlmostEqual(report['min_compensation_um'], low)
            self.assertAlmostEqual(report['max_compensation_um'], high)

    def test_mean_and_zero_gain(self):
        rows, _ = calculate([50]*360, CONFIG)
        self.assertTrue(all(abs(r[2]) < 1e-10 for r in rows))
        rows, _ = calculate(ERRORS, {**CONFIG,'gain':0})
        self.assertTrue(all(r[2] == 0 for r in rows))

    def test_limits(self):
        for patch in [{'gain':2}, {'gain':True}, {'z_mm':float('nan')}, {'nominal_radius_mm':-1}, {'max_compensation_um':1}, {'mode':'unknown'}, {'extra':1}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                calculate(ERRORS, {**CONFIG, **patch})

    def write_input(self, path, rows):
        with path.open('w', newline='') as f:
            w=csv.writer(f); w.writerow(['angle_deg','radial_error_um']); w.writerows(rows)

    def test_invalid_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'in.csv'
            for rows in [list(enumerate(ERRORS))[:-1], [(0,0)]*360, [(a,float('nan')) for a in range(360)], [(a+.5,0) for a in range(360)]]:
                self.write_input(p, rows)
                with self.assertRaises(ValueError): read_profile(p)

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'in.csv'; out=Path(d)/'out'
            self.write_input(p, reversed(list(enumerate(ERRORS))))
            self.assertEqual(read_profile(p), ERRORS)
            run(p, CONFIG, out)
            with (out/'compensated_profile.csv').open() as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),360)
            self.assertEqual(float(rows[0]['z_mm']),2)
            dxf=(out/'compensated_profile.dxf').read_text().splitlines()
            pairs=list(zip(dxf[::2],dxf[1::2]))
            self.assertEqual(sum(code=='10' for code,_ in pairs),360)
            self.assertIn(('70','1'),pairs)
            self.assertIn(('38','2'),pairs)
            self.assertEqual(len(json.loads((out/'report.json').read_text())['input_sha256']),64)
            with self.assertRaises(ValueError): run(p,CONFIG,out)

if __name__ == '__main__': unittest.main()
