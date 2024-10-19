package main

import (
	"fmt"
	"sort"
)

func main() {
	lst := []int{3, 4, 5, 2, 5, 2, 3}

	// 去重
	uniqueMap := make(map[int]bool)
	for _, num := range lst {
		uniqueMap[num] = true
	}

	uniqueList := []int{}
	for num := range uniqueMap {
		uniqueList = append(uniqueList, num)
	}

	// 排序
	sort.Ints(uniqueList)

	fmt.Println(uniqueList)
}
