import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.eulerspiral import *


class TestEulerSpiral(unittest.TestCase):
    def test_curvature(self):
        # straight line - has no curvature
        line = EulerSpiral(0)
        kappa0 = 0
        result = (0, 0)
        self.assertEqual(result, line.curvature(s=1, kappa0=kappa0))
        self.assertEqual(result, line.curvature(s=100, kappa0=kappa0))

        # arc - constant curvature
        arc = EulerSpiral(0)
        kappa0 = 2
        result = (2, 0)
        self.assertEqual(result, arc.curvature(s=1, kappa0=kappa0))
        self.assertEqual(result, arc.curvature(s=100, kappa0=kappa0))

        # spiral - varying curvature
        spiral = EulerSpiral(1)
        kappa0 = 2
        s1 = 0
        s2 = 5
        self.assertEqual((2, 1), spiral.curvature(s=s1, kappa0=kappa0))
        self.assertEqual((7, 1), spiral.curvature(s=s2, kappa0=kappa0))

    def test_createFromLengthAndCurvature(self):
        curvStart = 1
        curvEnd = 5

        # length = 0
        length = 0
        spiral = EulerSpiral.create_from_length_and_curvature(length, curvStart, curvEnd)
        self.assertEqual(0, spiral._gamma)

        # length != 0
        length = 4
        spiral = EulerSpiral.create_from_length_and_curvature(length, curvStart, curvEnd)
        self.assertEqual(1, spiral._gamma)

    def test_calc(self):
        # parameters at starting point - x0, y0, curvature kappa0, angle of tangent theta0
        x0 = 0
        y0 = 0
        kappa0 = 0
        theta0 = 3
        s = 2

        # straight line
        line = EulerSpiral(0)
        result = line.calc(s=s, x0=x0, y0=y0, kappa0=kappa0, theta0=theta0)
        expected = (-1.979984993, 0.2822400161, 3, (0, 0))
        for i in range(len(expected)):
            self.assertAlmostEqual(expected[i], result[i])

        # arc
        arc = EulerSpiral(0)
        x0 = 1
        y0 = 1
        kappa0 = 1
        s = 2
        result = arc.calc(s=s, x0=x0, y0=y0, kappa0=kappa0, theta0=theta0)
        expected = (-0.100044283, -0.273654682, 5, (1, 0))
        for i in range(len(expected)):
            self.assertAlmostEqual(expected[i], result[i])

    def test_calc_fresnel_integral(self):
        # spiral
        s = 1.4
        kappa0 = 2
        theta0 = 1.5
        C0 = 4 + 1j * 2

        spiral = EulerSpiral(1.2)
        result = spiral._calc_fresnel_integral(s=s, kappa0=kappa0, theta0=theta0, C0=C0)
        Cs_real = 3.356510087
        Cs_imag = 1.956997971
        self.assertAlmostEqual(Cs_real, result.real)
        self.assertAlmostEqual(Cs_imag, result.imag)


if __name__ == '__main__':
    unittest.main()
