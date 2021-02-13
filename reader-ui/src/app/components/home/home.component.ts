import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AppService } from 'src/app/services/app.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {


  base64textString = '';
  fileData: any;
  showLoader = false;
  fileName: string;
  

  constructor(
    private appService: AppService,
    private router: Router,
  ) { }

  ngOnInit(): void {
  }

  makeCall(fileData: any) {
    this.showLoader = true;
    // console.log(fileData);
    const req = {
      "request": fileData
    }
    // console.log(req)
    this.appService.uploadFile(req).subscribe(val => {
      if (val) {
        this.showLoader = false;
        this.fileName = this.fileData.name;
        this.navigatePage();
        // console.log('Upload successful');
      }
    }, (error) => {
      this.showLoader = false;
      alert(error)
    })
  }

  onFileChanged(event: any) {

    if (event && event.target && event.target.files.length > 0) {
      this.fileData = event.target.files[0];
      // console.log(this.fileData);
      if (this.fileData) {
        const reader = new FileReader();
        reader.onload = this.handleReaderLoaded.bind(this);
        reader.readAsBinaryString(this.fileData);
      }
    }
  }

  convertFile() {
    this.appService.convertFile().subscribe(val => {
      // console.log(val)
      this.router.navigate(['book']);
    })
  }

  handleReaderLoaded(e: any) {
    this.base64textString = btoa(e.target.result);
    const obj = {
      'bytes': JSON.stringify(this.base64textString),
      'filename': this.fileData.name,
      'size': this.fileData.size / 1000
    }
    this.makeCall(obj);
    // console.log(this.base64textString)
    // this.imgSrc = 'data:image/png;base64,' + this.base64textString;
  }

  navigatePage() {
    this.router.navigate(['book'])
  }

}
