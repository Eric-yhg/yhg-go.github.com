package main

import "fmt"

func main() {
	a := 100
	b := 200
	if a > 90 {
		if b > 1000 {
			fmt.Println(a, b)
		} else {
			fmt.Println(b, a)
		}
	}
	c := false
	d := true
	if c && d {
		fmt.Println("its ok")
	} else {
		fmt.Println("its false")
	}
}




