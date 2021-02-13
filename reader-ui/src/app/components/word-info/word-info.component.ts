import { Component, Input, OnInit } from '@angular/core';
import { UtilityService } from 'src/app/services/utility.service';

@Component({
  selector: 'app-word-info',
  templateUrl: './word-info.component.html',
  styleUrls: ['./word-info.component.scss']
})
export class WordInfoComponent implements OnInit {


  wordData: any;
  wordTree: any;

  @Input() set wordDetails(data: any) {
    this.wordData = JSON.parse(JSON.stringify(data));
    // console.log('Data received:', this.wordData)
    this.formTree();
  }

  constructor(
    private utilityService: UtilityService
  ) { 
  }

  ngOnInit(): void {
  }

  formTree() {
    this.wordTree = [];
    if (this.utilityService.isDefined(this.wordData) && this.utilityService.isArrayDefined(this.wordData.children)) {
      const obj = {
        "word": this.wordData.word,
        "score": this.wordData.score,
        "cefr": this.wordData.cefr,
        "sentence": this.wordData.sentence
      }
      this.wordTree = this.wordData.children;
      this.wordTree.push(obj)
      // console.log(this.wordTree)
    } else {
      this.wordTree = undefined;
    }
  }

  showTitle(index: number): any {
    if (index === 0) {
      return "Original Word";
    } else if (index + 1 < this.wordTree.length) {
      return "Iteration " + (index);
    } else {
      return "Final Word";
    }
  }

}
