using System;
using System.IO;
using System.Linq;
using System.Globalization;
using System.Collections.Generic;

public class DistanceRow { public string V, R; public double C; }

public class DistanceRangeAggregation {
    static double Number(string s) { return double.Parse(s.Trim().Replace(",", "."), CultureInfo.InvariantCulture); }
    static string Range(double x) {
        if (x <= 1) return "<= 1"; if (x <= 2) return "> 1 y <= 2"; if (x <= 5) return "> 2 y <= 5";
        if (x <= 10) return "> 5 y <= 10"; if (x <= 20) return "> 10 y <= 20"; if (x <= 50) return "> 20 y <= 50";
        if (x <= 100) return "> 50 y <= 100"; if (x <= 300) return "> 100 y <= 300"; return "> 300";
    }
    static double Quantile(List<double> a, double p) {
        a.Sort(); double x = (a.Count - 1) * p; int lo = (int)Math.Floor(x), hi = (int)Math.Ceiling(x);
        return a[lo] + (x - lo) * (a[hi] - a[lo]);
    }
    static readonly string[] Ranges = { "<= 1", "> 1 y <= 2", "> 2 y <= 5", "> 5 y <= 10", "> 10 y <= 20", "> 20 y <= 50", "> 50 y <= 100", "> 100 y <= 300", "> 300" };
    public static void Run() {
        var rows = new List<DistanceRow>();
        foreach (var line in File.ReadLines("data/datos_operativa.csv").Skip(1)) {
            var f = line.Split(';'); int year = int.Parse(f[3].Substring(0, 4)); double km = Number(f[5]) / 1000, liters = Number(f[7]) / 1000;
            if ((year == 2024 || year == 2025) && km > 0 && liters > 0) rows.Add(new DistanceRow { V = f[0], R = Range(km), C = 100 * liters / km });
        }
        var eligible = new HashSet<string>(rows.GroupBy(x => x.V).Where(g => g.Count() >= 100).Select(g => g.Key));
        rows = rows.Where(x => eligible.Contains(x.V)).ToList();
        var lines = new List<string> { "type;vehicle;range;n;median;P75;P90;P95" };
        foreach (var g in rows.GroupBy(x => x.V).OrderBy(g => int.Parse(g.Key))) { var a = g.Select(x => x.C).ToList(); lines.Add("global;" + g.Key + ";;" + a.Count + ";" + Quantile(a, .5).ToString("F6", CultureInfo.InvariantCulture) + ";;;;"); }
        foreach (var g in rows.GroupBy(x => x.V + "|" + x.R).OrderBy(g => int.Parse(g.First().V)).ThenBy(g => Array.IndexOf(Ranges, g.First().R))) { var a = g.Select(x => x.C).ToList(); lines.Add("range;" + g.First().V + ";" + g.First().R + ";" + a.Count + ";" + Quantile(a, .5).ToString("F6", CultureInfo.InvariantCulture) + ";" + Quantile(a, .75).ToString("F6", CultureInfo.InvariantCulture) + ";" + Quantile(a, .9).ToString("F6", CultureInfo.InvariantCulture) + ";" + Quantile(a, .95).ToString("F6", CultureInfo.InvariantCulture)); }
        foreach (var g in rows.GroupBy(x => x.R).OrderBy(g => Array.IndexOf(Ranges, g.Key))) lines.Add("total;;" + g.Key + ";" + g.Count() + ";;;;");
        File.WriteAllLines("data/analisis_distancia_2024_2025.csv", lines);
        Console.WriteLine("valid=" + rows.Count + " vehicles=" + eligible.Count);
    }
}
