//package main

//func main() {
//	a := 100
//	b := 200
//	var ret int
//	ret = max(a, b)
//	fmt.Printf("最大值是 : %d\n", ret)
//}
//
//func max(num1, num2 int) int {
//	/* 声明局部变量 */
//	var result int
//
//	if num1 > num2 {
//		result = num1
//	} else {
//		result = num2
//	}
//	return result
//}

package main

import "fmt"

/* 声明全局变量 */
var a int = 20

func main() {
	/* main 函数中声明局部变量 */
	var a int = 10
	var b int = 20
	var c int = 0

	fmt.Printf("main()函数中 a = %d\n", a)
	c = sum(a, b)
	fmt.Printf("main()函数中 c = %d\n", c)
}

/* 函数定义-两数相加 */
func sum(a, b int) int {
	fmt.Printf("sum() 函数中 a = %d\n", a)
	fmt.Printf("sum() 函数中 b = %d\n", b)

	return a + b
}
