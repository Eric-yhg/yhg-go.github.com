package main

//func main() {
//	for true {
//		fmt.Print("这是一个测试")
//		time.Sleep(10)
//	}
//}

//
//func main() {
//	/* 定义局部变量 */
//	var i, j int
//
//	for i = 2; i < 1000; i++ {
//		for j = 2; j <= (i / j); j++ {
//			if i%j == 0 {
//				break // 如果发现因子，则不是素数
//			}
//		}
//		if j > (i / j) {
//			fmt.Printf("%d  是素数\n", i)
//		}
//	}
//}

import "fmt"

func main() {
	for m := 1; m < 10; m++ {
		/*    fmt.Printf("第%d次：\n",m) */
		for n := 1; n <= m; n++ {
			fmt.Printf("%dx%d=%d ", n, m, m*n)
		}
		fmt.Println("")
	}
}
