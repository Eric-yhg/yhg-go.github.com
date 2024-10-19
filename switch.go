package main

import "fmt"

func main() {
	a := 90
	//c := "yhg"

	switch {
	default:
		{
			fmt.Println("default")
		}
	case a > 100:
		fmt.Println("a > 100")
	case a < 70:
		fmt.Println("a < 80")
	}
}
