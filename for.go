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
```

这段代码是用Go语言编写的，主要包含了两个不同的代码块。第一个代码块是一个简单的无限循环，第二个代码块是一个计算素数的程序。

第一个代码块：

```Go
/*
    for true {
        fmt.Print("这是一个测试")
        time.Sleep(10)
    }
*/
```

这行代码是一个注释，它表示下面的代码是用于测试的无限循环。`fmt.Print("这是一个测试")`会输出一个字符串，`time.Sleep(10)`会暂停10毫秒（10 * 1000000ns）。

第二个代码块：

```Go
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

