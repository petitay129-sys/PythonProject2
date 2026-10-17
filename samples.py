# samples.py
"""Ready-made JabaiScript programs the user can load from the GUI."""

SAMPLES = {
    "Kumusta (print)": '''// Unang programa
estorya ngalan = "Kalibutan";
printa("Kumusta, " + ngalan + "!");
''',

    "para sa  (for)": '''// para sa = for
para sa (tibuok i = 1; i <= 5; i++) {
    printa("Ika-" + i + " nga higayon");
}
''',

    "sa matag usa nga naa sa sulod  (for in / of)": '''// sa matag usa nga naa sa sulod = for in / for of
tapok prutas = ["mangga", "saging", "papaya"];
sa matag usa nga naa sa sulod (estorya p : prutas) {
    printa(p);
}

// sa hugpong, ang makuha kay ang mga yawe (keys)
hugpong tawo = {ngalan: "Ana", edad: 20};
sa matag usa nga naa sa sulod (yawe : tawo) {
    printa(yawe + " -> " + tawo[yawe]);
}
''',

    "sa matag usa  (for each)": '''// sa matag usa = for each  (ang ikaduhang ngalan kay ang index)
tapok prutas = ["mangga", "saging", "papaya"];
sa matag usa (estorya p, i : prutas) {
    printa(i + ": " + p);
}
''',

    "habang  (while)": '''// habang = while
tibuok n = 3;
habang (n > 0) {
    printa("Countdown: " + n);
    n--;
}
printa("Tapos na!");
''',

    "gawin ... habang  (do-while)": '''// gawin = do  (modagan kausa bisan pa mali ang kondisyon)
tibuok k = 10;
gawin {
    printa("k = " + k);
    k++;
} habang (k < 3);
''',

    "undang ug padayon  (break / continue)": '''// padayon = continue, undang = break
para sa (tibuok i = 1; i <= 10; i++) {
    kung (i % 2 == 0) {
        padayon;          // laktawan ang even
    }
    kung (i > 7) {
        undang;           // undangon ang loop
    }
    printa(i);
}
''',

    "kung / kaha kung / kung dili  (if-else)": '''tibuok edad = 15;

kung (edad >= 18) {
    printa("Hamtong na");
} kaha kung (edad >= 13) {
    printa("Tin-edyer");
} kung dili {
    printa("Bata pa");
}
''',

    "pili  (switch)": '''tibuok adlaw = 3;

pili (adlaw) {
    kaso 1:
        printa("Lunes");
        undang;
    kaso 2:
        printa("Martes");
        undang;
    kaso 3:
        printa("Miyerkules");
        undang;
    lain:
        printa("Laing adlaw");
}
''',

    "Tanang datatype": '''tibuok edad = 18;
bahin presyo = 9.75;
estorya ngalan = "Juan";
tinuod-bakak oo = tinuod;
titik grado = 'A';
tapok numero = [1, 2, 3];
hugpong tawo = {ngalan: "Ana", edad: 20};
estorya wala = walaBai;

printa(edad, presyo, ngalan, oo, grado);
printa(numero);
printa(tawo);
printa(wala);
''',

    "Multiplication table (nested loops)": '''para sa (tibuok i = 1; i <= 3; i++) {
    estorya linya = "";
    para sa (tibuok j = 1; j <= 5; j++) {
        linya = linya + (i * j) + "\\t";
    }
    printa(linya);
}
''',
}
